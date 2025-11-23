"""
GitHub data collector.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from github import Github, GithubException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DataSource, RawData, DataSourceType, DataSourceStatus
from app.core.security import encryption_manager

logger = logging.getLogger(__name__)


class GitHubCollector:
    """Collector for GitHub data."""

    def __init__(self, data_source: DataSource):
        """
        Initialize GitHub collector.

        Args:
            data_source: DataSource instance with GitHub credentials
        """
        self.data_source = data_source

        # Decrypt access token
        access_token = encryption_manager.decrypt(data_source.access_token)
        self.client = Github(access_token)

    async def collect_all(
        self,
        db: AsyncSession,
        since: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """
        Collect all GitHub data.

        Args:
            db: Database session
            since: Collect data since this date

        Returns:
            Dict with collection statistics
        """
        if not since and self.data_source.last_sync_at:
            since = self.data_source.last_sync_at
        elif not since:
            # Default to last 30 days
            since = datetime.utcnow() - timedelta(days=30)

        stats = {
            "commits": 0,
            "pull_requests": 0,
            "issues": 0,
            "stars": 0,
        }

        try:
            # Get authenticated user
            user = self.client.get_user()

            # Collect commits
            commits_count = await self._collect_commits(db, user, since)
            stats["commits"] = commits_count

            # Collect pull requests
            prs_count = await self._collect_pull_requests(db, user, since)
            stats["pull_requests"] = prs_count

            # Collect issues
            issues_count = await self._collect_issues(db, user, since)
            stats["issues"] = issues_count

            # Collect stars
            stars_count = await self._collect_starred_repos(db, user, since)
            stats["stars"] = stars_count

            # Update data source status
            self.data_source.status = DataSourceStatus.ACTIVE
            self.data_source.last_sync_at = datetime.utcnow()
            self.data_source.sync_error = None

            await db.commit()

            logger.info(f"GitHub collection complete: {stats}")
            return stats

        except GithubException as e:
            logger.error(f"GitHub API error: {e}")
            self.data_source.status = DataSourceStatus.ERROR
            self.data_source.sync_error = str(e)
            await db.commit()
            raise

        except Exception as e:
            logger.error(f"Error collecting GitHub data: {e}")
            self.data_source.status = DataSourceStatus.ERROR
            self.data_source.sync_error = str(e)
            await db.commit()
            raise

    async def _collect_commits(
        self,
        db: AsyncSession,
        user: Any,
        since: datetime,
    ) -> int:
        """Collect user commits."""
        count = 0

        try:
            # Get user's repositories
            repos = user.get_repos()

            for repo in repos:
                try:
                    # Get commits by user
                    commits = repo.get_commits(author=user, since=since)

                    for commit in commits:
                        # Check if already collected
                        existing = await db.execute(
                            f"SELECT id FROM raw_data WHERE external_id = '{commit.sha}' "
                            f"AND data_source_id = {self.data_source.id}"
                        )
                        if existing.scalar():
                            continue

                        # Create raw data entry
                        raw_data = RawData(
                            data_source_id=self.data_source.id,
                            external_id=commit.sha,
                            data_type="github_commit",
                            content={
                                "sha": commit.sha,
                                "message": commit.commit.message,
                                "repository": repo.full_name,
                                "additions": commit.stats.additions if commit.stats else 0,
                                "deletions": commit.stats.deletions if commit.stats else 0,
                                "files_changed": len(commit.files) if commit.files else 0,
                                "url": commit.html_url,
                            },
                            timestamp=commit.commit.author.date,
                            metadata={
                                "repository_url": repo.html_url,
                                "repository_language": repo.language,
                            }
                        )

                        db.add(raw_data)
                        count += 1

                except Exception as e:
                    logger.warning(f"Error collecting commits from {repo.full_name}: {e}")
                    continue

            await db.commit()
            return count

        except Exception as e:
            logger.error(f"Error collecting commits: {e}")
            return count

    async def _collect_pull_requests(
        self,
        db: AsyncSession,
        user: Any,
        since: datetime,
    ) -> int:
        """Collect user pull requests."""
        count = 0

        try:
            # Search for user's PRs
            query = f"author:{user.login} type:pr created:>={since.strftime('%Y-%m-%d')}"
            issues = self.client.search_issues(query)

            for pr in issues:
                # Create raw data entry
                raw_data = RawData(
                    data_source_id=self.data_source.id,
                    external_id=str(pr.id),
                    data_type="github_pull_request",
                    content={
                        "number": pr.number,
                        "title": pr.title,
                        "body": pr.body,
                        "state": pr.state,
                        "repository": pr.repository.full_name,
                        "created_at": pr.created_at.isoformat(),
                        "closed_at": pr.closed_at.isoformat() if pr.closed_at else None,
                        "merged": pr.pull_request.merged_at is not None if pr.pull_request else False,
                        "url": pr.html_url,
                    },
                    timestamp=pr.created_at,
                    metadata={
                        "comments": pr.comments,
                        "repository_url": pr.repository.html_url,
                    }
                )

                db.add(raw_data)
                count += 1

            await db.commit()
            return count

        except Exception as e:
            logger.error(f"Error collecting pull requests: {e}")
            return count

    async def _collect_issues(
        self,
        db: AsyncSession,
        user: Any,
        since: datetime,
    ) -> int:
        """Collect user issues."""
        count = 0

        try:
            # Search for user's issues (excluding PRs)
            query = f"author:{user.login} type:issue created:>={since.strftime('%Y-%m-%d')}"
            issues = self.client.search_issues(query)

            for issue in issues:
                # Create raw data entry
                raw_data = RawData(
                    data_source_id=self.data_source.id,
                    external_id=str(issue.id),
                    data_type="github_issue",
                    content={
                        "number": issue.number,
                        "title": issue.title,
                        "body": issue.body,
                        "state": issue.state,
                        "repository": issue.repository.full_name,
                        "created_at": issue.created_at.isoformat(),
                        "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                        "url": issue.html_url,
                        "labels": [label.name for label in issue.labels],
                    },
                    timestamp=issue.created_at,
                    metadata={
                        "comments": issue.comments,
                        "repository_url": issue.repository.html_url,
                    }
                )

                db.add(raw_data)
                count += 1

            await db.commit()
            return count

        except Exception as e:
            logger.error(f"Error collecting issues: {e}")
            return count

    async def _collect_starred_repos(
        self,
        db: AsyncSession,
        user: Any,
        since: datetime,
    ) -> int:
        """Collect starred repositories."""
        count = 0

        try:
            starred = user.get_starred()

            for repo in starred:
                # Note: GitHub API doesn't provide star timestamp, so we use repo creation date
                # This is a limitation of the API

                raw_data = RawData(
                    data_source_id=self.data_source.id,
                    external_id=str(repo.id),
                    data_type="github_star",
                    content={
                        "repository": repo.full_name,
                        "description": repo.description,
                        "language": repo.language,
                        "stars": repo.stargazers_count,
                        "forks": repo.forks_count,
                        "url": repo.html_url,
                        "topics": repo.get_topics(),
                    },
                    timestamp=repo.created_at,  # Using repo creation as proxy
                    metadata={
                        "repository_url": repo.html_url,
                    }
                )

                db.add(raw_data)
                count += 1

            await db.commit()
            return count

        except Exception as e:
            logger.error(f"Error collecting starred repos: {e}")
            return count


async def collect_github_data(
    data_source_id: int,
    db: AsyncSession,
) -> Dict[str, int]:
    """
    Collect GitHub data for a data source.

    Args:
        data_source_id: Data source ID
        db: Database session

    Returns:
        Collection statistics
    """
    # Get data source
    result = await db.execute(
        f"SELECT * FROM data_sources WHERE id = {data_source_id}"
    )
    data_source = result.scalar()

    if not data_source or data_source.source_type != DataSourceType.GITHUB:
        raise ValueError("Invalid data source")

    # Create collector and run collection
    collector = GitHubCollector(data_source)
    return await collector.collect_all(db)

<script lang="ts">
	import { onMount } from 'svelte';

	let stats = {
		dataSourcesConnected: 0,
		totalActivities: 0,
		insightsGenerated: 0,
		daysTracked: 0
	};

	onMount(async () => {
		// TODO: Fetch real stats from API
		stats = {
			dataSourcesConnected: 3,
			totalActivities: 1247,
			insightsGenerated: 42,
			daysTracked: 30
		};
	});
</script>

<svelte:head>
	<title>LifeMetrics - Dashboard</title>
</svelte:head>

<!-- Hero Section -->
<div class="hero bg-base-100 rounded-lg shadow-lg mb-8">
	<div class="hero-content text-center py-12">
		<div class="max-w-md">
			<h1 class="text-5xl font-bold">Welcome to LifeMetrics</h1>
			<p class="py-6">
				Your privacy-first AI-powered life analytics dashboard. Track, analyze, and optimize
				your digital life with complete data sovereignty.
			</p>
			<button class="btn btn-primary">Get Started</button>
		</div>
	</div>
</div>

<!-- Stats Overview -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
	<div class="stat bg-base-100 rounded-lg shadow">
		<div class="stat-figure text-primary">
			<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M13 10V3L4 14h7v7l9-11h-7z"
				/>
			</svg>
		</div>
		<div class="stat-title">Data Sources</div>
		<div class="stat-value text-primary">{stats.dataSourcesConnected}</div>
		<div class="stat-desc">Connected services</div>
	</div>

	<div class="stat bg-base-100 rounded-lg shadow">
		<div class="stat-figure text-secondary">
			<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
				/>
			</svg>
		</div>
		<div class="stat-title">Activities</div>
		<div class="stat-value text-secondary">{stats.totalActivities.toLocaleString()}</div>
		<div class="stat-desc">Total tracked events</div>
	</div>

	<div class="stat bg-base-100 rounded-lg shadow">
		<div class="stat-figure text-accent">
			<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
				/>
			</svg>
		</div>
		<div class="stat-title">AI Insights</div>
		<div class="stat-value text-accent">{stats.insightsGenerated}</div>
		<div class="stat-desc">Generated locally</div>
	</div>

	<div class="stat bg-base-100 rounded-lg shadow">
		<div class="stat-figure text-info">
			<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
				/>
			</svg>
		</div>
		<div class="stat-title">Days Tracked</div>
		<div class="stat-value text-info">{stats.daysTracked}</div>
		<div class="stat-desc">Continuous monitoring</div>
	</div>
</div>

<!-- Quick Actions -->
<div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
	<div class="card bg-base-100 shadow-lg">
		<div class="card-body">
			<h2 class="card-title">
				<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M12 6v6m0 0v6m0-6h6m-6 0H6"
					/>
				</svg>
				Connect Data Sources
			</h2>
			<p>Connect your GitHub, Twitter, Gmail, and other services to start tracking.</p>
			<div class="card-actions justify-end">
				<a href="/sources" class="btn btn-primary btn-sm">Add Source</a>
			</div>
		</div>
	</div>

	<div class="card bg-base-100 shadow-lg">
		<div class="card-body">
			<h2 class="card-title">
				<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
					/>
				</svg>
				View Analytics
			</h2>
			<p>Explore your productivity trends, emotion patterns, and insights.</p>
			<div class="card-actions justify-end">
				<a href="/dashboard" class="btn btn-secondary btn-sm">Open Dashboard</a>
			</div>
		</div>
	</div>
</div>

<!-- Privacy Notice -->
<div class="alert alert-success shadow-lg">
	<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
		<path
			stroke-linecap="round"
			stroke-linejoin="round"
			stroke-width="2"
			d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
		/>
	</svg>
	<div>
		<h3 class="font-bold">100% Privacy Guaranteed</h3>
		<div class="text-xs">
			All your data is stored locally. We use Ollama for AI analysis - no data ever leaves
			your machine.
		</div>
	</div>
</div>

<style>
	.stat {
		place-items: start;
	}
</style>

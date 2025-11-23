<script lang="ts">
	import { onMount } from 'svelte';

	let selectedPeriod = 'week';
	let loading = true;

	let todaySummary = {
		productivity: 75,
		emotion: 'positive',
		commits: 12,
		emails: 34,
		focusTime: 4.5
	};

	onMount(async () => {
		// TODO: Fetch real data from API
		setTimeout(() => {
			loading = false;
		}, 500);
	});

	function changePeriod(period: string) {
		selectedPeriod = period;
		// TODO: Fetch data for selected period
	}
</script>

<svelte:head>
	<title>Dashboard - LifeMetrics</title>
</svelte:head>

<!-- Page Header -->
<div class="mb-8">
	<h1 class="text-4xl font-bold mb-2">Analytics Dashboard</h1>
	<p class="text-base-content/60">Overview of your digital life metrics</p>
</div>

<!-- Period Selector -->
<div class="tabs tabs-boxed mb-6 bg-base-100 shadow-lg">
	<button
		class="tab {selectedPeriod === 'day' ? 'tab-active' : ''}"
		on:click={() => changePeriod('day')}
	>
		Today
	</button>
	<button
		class="tab {selectedPeriod === 'week' ? 'tab-active' : ''}"
		on:click={() => changePeriod('week')}
	>
		This Week
	</button>
	<button
		class="tab {selectedPeriod === 'month' ? 'tab-active' : ''}"
		on:click={() => changePeriod('month')}
	>
		This Month
	</button>
	<button
		class="tab {selectedPeriod === 'year' ? 'tab-active' : ''}"
		on:click={() => changePeriod('year')}
	>
		This Year
	</button>
</div>

{#if loading}
	<div class="flex justify-center items-center h-64">
		<span class="loading loading-spinner loading-lg text-primary"></span>
	</div>
{:else}
	<!-- Today's Summary -->
	<div class="card bg-gradient-to-r from-primary to-secondary text-primary-content shadow-lg mb-6">
		<div class="card-body">
			<h2 class="card-title text-2xl">Today's Summary</h2>
			<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
				<div>
					<div class="stat-title text-primary-content/70">Productivity Score</div>
					<div class="stat-value text-white">{todaySummary.productivity}%</div>
					<progress
						class="progress progress-success w-full"
						value={todaySummary.productivity}
						max="100"
					></progress>
				</div>
				<div>
					<div class="stat-title text-primary-content/70">Emotional State</div>
					<div class="stat-value text-white capitalize">{todaySummary.emotion}</div>
					<div class="badge badge-success gap-2 mt-2">
						<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
							<path
								fill-rule="evenodd"
								d="M10 18a8 8 0 100-16 8 8 0 000 16zM7 9a1 1 0 100-2 1 1 0 000 2zm7-1a1 1 0 11-2 0 1 1 0 012 0zm-.464 5.535a1 1 0 10-1.415-1.414 3 3 0 01-4.242 0 1 1 0 00-1.415 1.414 5 5 0 007.072 0z"
								clip-rule="evenodd"
							/>
						</svg>
						Feeling good
					</div>
				</div>
				<div>
					<div class="stat-title text-primary-content/70">Focus Time</div>
					<div class="stat-value text-white">{todaySummary.focusTime}h</div>
					<div class="text-sm text-primary-content/70 mt-2">
						{todaySummary.commits} commits • {todaySummary.emails} emails
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Main Content Grid -->
	<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
		<!-- Activity Chart -->
		<div class="card bg-base-100 shadow-lg">
			<div class="card-body">
				<h2 class="card-title">Activity Overview</h2>
				<div class="h-64 flex items-center justify-center bg-base-200 rounded-lg">
					<p class="text-base-content/50">Chart.js visualization will appear here</p>
				</div>
			</div>
		</div>

		<!-- Productivity Trends -->
		<div class="card bg-base-100 shadow-lg">
			<div class="card-body">
				<h2 class="card-title">Productivity Trends</h2>
				<div class="h-64 flex items-center justify-center bg-base-200 rounded-lg">
					<p class="text-base-content/50">D3.js visualization will appear here</p>
				</div>
			</div>
		</div>
	</div>

	<!-- AI Insights -->
	<div class="card bg-base-100 shadow-lg mb-6">
		<div class="card-body">
			<h2 class="card-title">
				<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
					/>
				</svg>
				AI-Generated Insights
			</h2>
			<div class="space-y-4 mt-4">
				<div class="alert alert-info">
					<svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
						<path
							fill-rule="evenodd"
							d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
							clip-rule="evenodd"
						/>
					</svg>
					<span
						>Your most productive hours are between 9 AM and 12 PM. Consider scheduling important
						tasks during this time.</span
					>
				</div>
				<div class="alert alert-success">
					<svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
						<path
							fill-rule="evenodd"
							d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
							clip-rule="evenodd"
						/>
					</svg>
					<span>Great work! You've maintained a consistent coding streak for 7 days.</span>
				</div>
				<div class="alert alert-warning">
					<svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
						<path
							fill-rule="evenodd"
							d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
							clip-rule="evenodd"
						/>
					</svg>
					<span
						>You've been responding to emails late at night. Consider setting boundaries for
						better work-life balance.</span
					>
				</div>
			</div>
		</div>
	</div>

	<!-- Recent Activities -->
	<div class="card bg-base-100 shadow-lg">
		<div class="card-body">
			<h2 class="card-title">Recent Activities</h2>
			<div class="overflow-x-auto">
				<table class="table">
					<thead>
						<tr>
							<th>Time</th>
							<th>Activity</th>
							<th>Source</th>
							<th>Impact</th>
						</tr>
					</thead>
					<tbody>
						<tr>
							<td>2 hours ago</td>
							<td>Committed feature: Add user dashboard</td>
							<td>
								<span class="badge badge-primary">GitHub</span>
							</td>
							<td>
								<div class="badge badge-success">High</div>
							</td>
						</tr>
						<tr>
							<td>3 hours ago</td>
							<td>Sent 12 emails</td>
							<td>
								<span class="badge badge-secondary">Gmail</span>
							</td>
							<td>
								<div class="badge badge-info">Medium</div>
							</td>
						</tr>
						<tr>
							<td>5 hours ago</td>
							<td>Attended meeting: Sprint Planning</td>
							<td>
								<span class="badge badge-accent">Calendar</span>
							</td>
							<td>
								<div class="badge badge-warning">Low</div>
							</td>
						</tr>
					</tbody>
				</table>
			</div>
		</div>
	</div>
{/if}

<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';

	let theme = 'light';

	onMount(() => {
		// Load theme from localStorage
		const savedTheme = localStorage.getItem('theme') || 'light';
		theme = savedTheme;
		document.documentElement.setAttribute('data-theme', theme);
	});

	function toggleTheme() {
		theme = theme === 'light' ? 'dark' : 'light';
		document.documentElement.setAttribute('data-theme', theme);
		localStorage.setItem('theme', theme);
	}
</script>

<div class="min-h-screen bg-base-200">
	<!-- Navbar -->
	<div class="navbar bg-base-100 shadow-lg">
		<div class="flex-1">
			<a href="/" class="btn btn-ghost text-xl">
				LifeMetrics
			</a>
		</div>
		<div class="flex-none gap-2">
			<!-- Theme toggle -->
			<button class="btn btn-ghost btn-circle" on:click={toggleTheme}>
				{#if theme === 'light'}
					<svg
						class="w-5 h-5"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
						/>
					</svg>
				{:else}
					<svg
						class="w-5 h-5"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
						/>
					</svg>
				{/if}
			</button>

			<!-- User menu -->
			<div class="dropdown dropdown-end">
				<label tabindex="0" class="btn btn-ghost btn-circle avatar">
					<div class="w-10 rounded-full bg-primary text-primary-content flex items-center justify-center">
						<span class="text-xl">U</span>
					</div>
				</label>
				<ul
					tabindex="0"
					class="mt-3 z-[1] p-2 shadow menu menu-sm dropdown-content bg-base-100 rounded-box w-52"
				>
					<li><a href="/profile">Profile</a></li>
					<li><a href="/settings">Settings</a></li>
					<li><a href="/privacy">Privacy</a></li>
					<li><a>Logout</a></li>
				</ul>
			</div>
		</div>
	</div>

	<!-- Main content -->
	<div class="container mx-auto px-4 py-8">
		<slot />
	</div>

	<!-- Footer -->
	<footer class="footer footer-center p-4 bg-base-100 text-base-content mt-8">
		<div>
			<p>
				LifeMetrics - Privacy-first AI life analytics.
				<span class="text-success">All data stored locally.</span>
			</p>
		</div>
	</footer>
</div>

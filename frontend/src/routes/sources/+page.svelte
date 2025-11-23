<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import api from '$lib/api';

	interface DataSource {
		id: number;
		source_type: string;
		status: string;
		last_sync_at: string | null;
		sync_error: string | null;
	}

	let dataSources: DataSource[] = [];
	let loading = true;
	let error = '';
	let successMessage = '';

	// Available data sources with icons and descriptions
	const availableSources = [
		{
			type: 'github',
			name: 'GitHub',
			icon: '🐙',
			description: 'コミット、PR、Issue、スターの分析',
			color: 'bg-gray-800'
		},
		{
			type: 'twitter',
			name: 'Twitter / X',
			icon: '🐦',
			description: 'ツイート、いいねの感情分析',
			color: 'bg-blue-500'
		},
		{
			type: 'gmail',
			name: 'Gmail',
			icon: '📧',
			description: 'メール送受信パターンの分析',
			color: 'bg-red-500'
		},
		{
			type: 'calendar',
			name: 'Google Calendar',
			icon: '📅',
			description: 'スケジュールと時間管理の分析',
			color: 'bg-green-500'
		}
	];

	onMount(async () => {
		// Check for OAuth callback success/error
		const success = $page.url.searchParams.get('success');
		const errorParam = $page.url.searchParams.get('error');

		if (success) {
			successMessage = `✅ ${success}の接続に成功しました！`;
			// Clear URL parameters
			window.history.replaceState({}, '', '/sources');
		} else if (errorParam) {
			error = `❌ ${errorParam}の接続に失敗しました。再試行してください。`;
			window.history.replaceState({}, '', '/sources');
		}

		await loadDataSources();
	});

	async function loadDataSources() {
		try {
			loading = true;
			error = '';
			const response = await fetch('/api/data-sources', {
				headers: {
					Authorization: `Bearer ${api.token}`
				}
			});

			if (!response.ok) {
				if (response.status === 401) {
					goto('/login');
					return;
				}
				throw new Error('データソースの取得に失敗しました');
			}

			dataSources = await response.json();
		} catch (e) {
			error = e instanceof Error ? e.message : '不明なエラーが発生しました';
		} finally {
			loading = false;
		}
	}

	async function connectSource(sourceType: string) {
		try {
			error = '';
			successMessage = '';

			// For Google services, need to specify the service
			if (sourceType === 'gmail' || sourceType === 'calendar') {
				window.location.href = `/api/oauth/google/authorize?service=${sourceType}`;
			} else {
				window.location.href = `/api/oauth/${sourceType}/authorize`;
			}
		} catch (e) {
			error = e instanceof Error ? e.message : '接続の開始に失敗しました';
		}
	}

	async function disconnectSource(sourceType: string) {
		if (!confirm(`${sourceType}の接続を解除しますか？関連データは削除されません。`)) {
			return;
		}

		try {
			error = '';
			successMessage = '';

			const response = await fetch(`/api/oauth/disconnect/${sourceType}`, {
				method: 'DELETE',
				headers: {
					Authorization: `Bearer ${api.token}`
				}
			});

			if (!response.ok) {
				throw new Error('接続の解除に失敗しました');
			}

			successMessage = `✅ ${sourceType}の接続を解除しました`;
			await loadDataSources();
		} catch (e) {
			error = e instanceof Error ? e.message : '接続の解除に失敗しました';
		}
	}

	async function triggerSync(sourceId: number, sourceType: string) {
		try {
			error = '';
			successMessage = '';

			const response = await fetch(`/api/data-sources/${sourceId}/sync`, {
				method: 'POST',
				headers: {
					Authorization: `Bearer ${api.token}`
				}
			});

			if (!response.ok) {
				throw new Error('同期の開始に失敗しました');
			}

			successMessage = `✅ ${sourceType}の同期を開始しました`;
			await loadDataSources();
		} catch (e) {
			error = e instanceof Error ? e.message : '同期の開始に失敗しました';
		}
	}

	function isConnected(sourceType: string): DataSource | undefined {
		return dataSources.find((ds) => ds.source_type === sourceType);
	}

	function getStatusBadge(status: string): { text: string; class: string } {
		switch (status) {
			case 'active':
				return { text: '接続済み', class: 'badge-success' };
			case 'error':
				return { text: 'エラー', class: 'badge-error' };
			case 'syncing':
				return { text: '同期中', class: 'badge-info' };
			default:
				return { text: status, class: 'badge-ghost' };
		}
	}

	function formatLastSync(lastSync: string | null): string {
		if (!lastSync) return '未同期';

		const date = new Date(lastSync);
		const now = new Date();
		const diffMs = now.getTime() - date.getTime();
		const diffMins = Math.floor(diffMs / 60000);

		if (diffMins < 1) return 'たった今';
		if (diffMins < 60) return `${diffMins}分前`;
		if (diffMins < 1440) return `${Math.floor(diffMins / 60)}時間前`;
		return `${Math.floor(diffMins / 1440)}日前`;
	}
</script>

<svelte:head>
	<title>データソース管理 - LifeMetrics</title>
</svelte:head>

<div class="container mx-auto px-4 py-8 max-w-6xl">
	<!-- Header -->
	<div class="mb-8">
		<h1 class="text-4xl font-bold mb-2">データソース管理</h1>
		<p class="text-base-content/60">
			各種サービスを接続して、あなたのライフログを統合的に分析します
		</p>
	</div>

	<!-- Alert Messages -->
	{#if error}
		<div class="alert alert-error mb-6">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="stroke-current shrink-0 h-6 w-6"
				fill="none"
				viewBox="0 0 24 24"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
				/>
			</svg>
			<span>{error}</span>
		</div>
	{/if}

	{#if successMessage}
		<div class="alert alert-success mb-6">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="stroke-current shrink-0 h-6 w-6"
				fill="none"
				viewBox="0 0 24 24"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
				/>
			</svg>
			<span>{successMessage}</span>
		</div>
	{/if}

	<!-- Privacy Notice -->
	<div class="alert alert-info mb-8">
		<svg
			xmlns="http://www.w3.org/2000/svg"
			fill="none"
			viewBox="0 0 24 24"
			class="stroke-current shrink-0 w-6 h-6"
		>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
			/>
		</svg>
		<div>
			<h3 class="font-bold">プライバシー保護</h3>
			<div class="text-sm">
				すべてのデータはローカル環境に保存され、外部に送信されることはありません。
				OAuth トークンは暗号化されて保存されます。
			</div>
		</div>
	</div>

	<!-- Data Sources Grid -->
	{#if loading}
		<div class="flex justify-center items-center py-20">
			<span class="loading loading-spinner loading-lg"></span>
		</div>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
			{#each availableSources as source}
				{@const connected = isConnected(source.type)}
				{@const statusBadge = connected ? getStatusBadge(connected.status) : null}

				<div class="card bg-base-100 shadow-xl hover:shadow-2xl transition-shadow">
					<div class="card-body">
						<!-- Header -->
						<div class="flex items-start justify-between mb-4">
							<div class="flex items-center gap-3">
								<div class="text-4xl {source.color} rounded-lg p-3 bg-opacity-10">
									{source.icon}
								</div>
								<div>
									<h2 class="card-title">{source.name}</h2>
									{#if connected && statusBadge}
										<div class="badge {statusBadge.class} badge-sm mt-1">
											{statusBadge.text}
										</div>
									{/if}
								</div>
							</div>
						</div>

						<!-- Description -->
						<p class="text-sm text-base-content/60 mb-4">{source.description}</p>

						<!-- Connection Info -->
						{#if connected}
							<div class="bg-base-200 rounded-lg p-3 mb-4 text-sm space-y-1">
								<div class="flex justify-between">
									<span class="text-base-content/60">最終同期:</span>
									<span class="font-medium">{formatLastSync(connected.last_sync_at)}</span>
								</div>
								{#if connected.sync_error}
									<div class="text-error text-xs mt-2">
										エラー: {connected.sync_error}
									</div>
								{/if}
							</div>
						{/if}

						<!-- Actions -->
						<div class="card-actions justify-end gap-2">
							{#if connected}
								<button
									class="btn btn-sm btn-outline"
									on:click={() => triggerSync(connected.id, source.name)}
									disabled={connected.status === 'syncing'}
								>
									{#if connected.status === 'syncing'}
										<span class="loading loading-spinner loading-xs"></span>
										同期中...
									{:else}
										🔄 同期
									{/if}
								</button>
								<button
									class="btn btn-sm btn-error btn-outline"
									on:click={() => disconnectSource(source.type)}
								>
									🔌 切断
								</button>
							{:else}
								<button
									class="btn btn-sm btn-primary"
									on:click={() => connectSource(source.type)}
								>
									🔗 接続
								</button>
							{/if}
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}

	<!-- Additional Info -->
	<div class="mt-12 prose max-w-none">
		<h2>データソースについて</h2>
		<div class="grid md:grid-cols-2 gap-6 not-prose">
			<div class="card bg-base-200">
				<div class="card-body">
					<h3 class="card-title text-lg">自動同期</h3>
					<p class="text-sm text-base-content/70">
						接続されたデータソースは1時間ごとに自動的に同期されます。
						手動同期も可能です。
					</p>
				</div>
			</div>

			<div class="card bg-base-200">
				<div class="card-body">
					<h3 class="card-title text-lg">データの削除</h3>
					<p class="text-sm text-base-content/70">
						データソースを切断しても、既に収集したデータは削除されません。
						データの削除は設定ページから行えます。
					</p>
				</div>
			</div>
		</div>
	</div>
</div>

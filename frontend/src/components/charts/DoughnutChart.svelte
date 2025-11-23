<script lang="ts">
	import { onMount } from 'svelte';
	import { Chart, registerables } from 'chart.js';

	Chart.register(...registerables);

	export let data: { labels: string[]; datasets: any[] };
	export let title: string = '';
	export let height: number = 300;

	let canvas: HTMLCanvasElement;
	let chart: Chart;

	onMount(() => {
		const ctx = canvas.getContext('2d');
		if (!ctx) return;

		chart = new Chart(ctx, {
			type: 'doughnut',
			data: data,
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					legend: {
						position: 'right'
					},
					title: {
						display: !!title,
						text: title
					}
				}
			}
		});

		return () => {
			chart.destroy();
		};
	});

	// Update chart when data changes
	$: if (chart && data) {
		chart.data = data;
		chart.update();
	}
</script>

<div style="height: {height}px">
	<canvas bind:this={canvas}></canvas>
</div>

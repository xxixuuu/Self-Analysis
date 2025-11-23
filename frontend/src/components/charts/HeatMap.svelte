<script lang="ts">
	import { onMount } from 'svelte';
	import * as d3 from 'd3';

	export let data: Array<{ date: string; hour: number; value: number }>;
	export let width = 900;
	export let height = 400;

	let svg: SVGSVGElement;

	onMount(() => {
		if (!data || data.length === 0) return;

		// Clear existing content
		d3.select(svg).selectAll('*').remove();

		// Margins
		const margin = { top: 50, right: 50, bottom: 50, left: 50 };
		const innerWidth = width - margin.left - margin.right;
		const innerHeight = height - margin.top - margin.bottom;

		// Create SVG
		const svgSelection = d3
			.select(svg)
			.attr('width', width)
			.attr('height', height)
			.attr('viewBox', [0, 0, width, height]);

		const g = svgSelection.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

		// Get unique dates and hours
		const dates = Array.from(new Set(data.map((d) => d.date))).sort();
		const hours = Array.from(new Set(data.map((d) => d.hour))).sort((a, b) => a - b);

		// Scales
		const xScale = d3.scaleBand().domain(dates).range([0, innerWidth]).padding(0.05);

		const yScale = d3.scaleBand().domain(hours.map(String)).range([0, innerHeight]).padding(0.05);

		const colorScale = d3
			.scaleSequential()
			.interpolator(d3.interpolateYlOrRd)
			.domain([0, d3.max(data, (d) => d.value) || 1]);

		// Create cells
		g.selectAll('rect')
			.data(data)
			.join('rect')
			.attr('x', (d) => xScale(d.date) || 0)
			.attr('y', (d) => yScale(String(d.hour)) || 0)
			.attr('width', xScale.bandwidth())
			.attr('height', yScale.bandwidth())
			.attr('fill', (d) => colorScale(d.value))
			.attr('rx', 4)
			.append('title')
			.text((d) => `${d.date} ${d.hour}:00\nValue: ${d.value.toFixed(2)}`);

		// X axis
		const xAxis = d3.axisBottom(xScale).tickValues(
			dates.filter((d, i) => i % Math.ceil(dates.length / 10) === 0) // Show every nth date
		);

		g.append('g')
			.attr('transform', `translate(0,${innerHeight})`)
			.call(xAxis)
			.selectAll('text')
			.attr('transform', 'rotate(-45)')
			.style('text-anchor', 'end');

		// Y axis
		const yAxis = d3.axisLeft(yScale);

		g.append('g').call(yAxis);

		// Labels
		g.append('text')
			.attr('x', innerWidth / 2)
			.attr('y', -20)
			.attr('text-anchor', 'middle')
			.style('font-size', '16px')
			.style('font-weight', 'bold')
			.text('Activity Heatmap');

		g.append('text')
			.attr('x', innerWidth / 2)
			.attr('y', innerHeight + 45)
			.attr('text-anchor', 'middle')
			.text('Date');

		g.append('text')
			.attr('transform', 'rotate(-90)')
			.attr('x', -innerHeight / 2)
			.attr('y', -35)
			.attr('text-anchor', 'middle')
			.text('Hour');

		// Legend
		const legendWidth = 300;
		const legendHeight = 10;

		const legendScale = d3
			.scaleLinear()
			.domain(colorScale.domain())
			.range([0, legendWidth]);

		const legend = g
			.append('g')
			.attr('transform', `translate(${innerWidth - legendWidth},${innerHeight + 40})`);

		// Legend gradient
		const defs = svgSelection.append('defs');
		const gradient = defs
			.append('linearGradient')
			.attr('id', 'heatmap-gradient')
			.attr('x1', '0%')
			.attr('x2', '100%');

		gradient
			.selectAll('stop')
			.data(
				d3.range(0, 1.01, 0.1).map((t) => ({
					offset: `${t * 100}%`,
					color: colorScale(legendScale.invert(t * legendWidth))
				}))
			)
			.join('stop')
			.attr('offset', (d) => d.offset)
			.attr('stop-color', (d) => d.color);

		legend
			.append('rect')
			.attr('width', legendWidth)
			.attr('height', legendHeight)
			.style('fill', 'url(#heatmap-gradient)');

		legend
			.append('g')
			.attr('transform', `translate(0,${legendHeight})`)
			.call(
				d3
					.axisBottom(legendScale)
					.ticks(5)
					.tickFormat((d) => d.toFixed(1))
			);
	});

	// Redraw when data changes
	$: if (svg && data) {
		onMount();
	}
</script>

<div class="heatmap">
	<svg bind:this={svg} class="w-full"></svg>
</div>

<style>
	.heatmap {
		width: 100%;
	}
</style>

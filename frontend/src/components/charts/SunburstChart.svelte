<script lang="ts">
	import { onMount } from 'svelte';
	import * as d3 from 'd3';

	export let data: {
		name: string;
		value?: number;
		children?: any[];
	};
	export let width = 600;
	export let height = 600;

	let svg: SVGSVGElement;

	onMount(() => {
		if (!data) return;

		// Clear existing content
		d3.select(svg).selectAll('*').remove();

		const radius = Math.min(width, height) / 2;

		// Create SVG
		const svgSelection = d3
			.select(svg)
			.attr('width', width)
			.attr('height', height)
			.attr('viewBox', [0, 0, width, height])
			.style('font', '12px sans-serif');

		const g = svgSelection
			.append('g')
			.attr('transform', `translate(${width / 2},${height / 2})`);

		// Create hierarchy
		const root = d3
			.hierarchy(data)
			.sum((d: any) => d.value || 0)
			.sort((a, b) => (b.value || 0) - (a.value || 0));

		// Create partition layout
		const partition = d3.partition<any>().size([2 * Math.PI, radius]);

		partition(root);

		// Color scale
		const color = d3.scaleOrdinal(d3.schemeCategory10);

		// Arc generator
		const arc = d3
			.arc<any>()
			.startAngle((d) => d.x0)
			.endAngle((d) => d.x1)
			.padAngle((d) => Math.min((d.x1 - d.x0) / 2, 0.005))
			.padRadius(radius / 2)
			.innerRadius((d) => d.y0)
			.outerRadius((d) => d.y1 - 1);

		// Create paths
		const path = g
			.selectAll('path')
			.data(root.descendants().filter((d) => d.depth))
			.join('path')
			.attr('fill', (d: any) => {
				while (d.depth > 1) d = d.parent;
				return color(d.data.name);
			})
			.attr('fill-opacity', (d: any) => (arcVisible(d.current) ? (d.children ? 0.6 : 0.4) : 0))
			.attr('d', (d: any) => arc(d));

		// Add tooltips
		path.append('title').text(
			(d: any) =>
				`${d
					.ancestors()
					.map((d: any) => d.data.name)
					.reverse()
					.join('/')}\n${d.value?.toFixed(2) || 0}`
		);

		// Make paths clickable for zoom
		path
			.filter((d: any) => d.children)
			.style('cursor', 'pointer')
			.on('click', clicked);

		// Add labels
		const label = g
			.selectAll('text')
			.data(root.descendants().filter((d) => d.depth && ((d.y0 + d.y1) / 2) * (d.x1 - d.x0) > 10))
			.join('text')
			.attr('transform', function (d: any) {
				const x = (((d.x0 + d.x1) / 2) * 180) / Math.PI;
				const y = (d.y0 + d.y1) / 2;
				return `rotate(${x - 90}) translate(${y},0) rotate(${x < 180 ? 0 : 180})`;
			})
			.attr('dy', '0.35em')
			.attr('fill-opacity', (d: any) => +labelVisible(d.current))
			.text((d: any) => d.data.name)
			.style('font-size', '10px');

		// Center circle for navigation
		const parent = g
			.append('circle')
			.datum(root)
			.attr('r', radius)
			.attr('fill', 'none')
			.attr('pointer-events', 'all')
			.on('click', clicked);

		// Click handler for zoom
		function clicked(event: any, p: any) {
			parent.datum(p.parent || root);

			root.each(
				(d: any) =>
					(d.target = {
						x0: Math.max(0, Math.min(1, (d.x0 - p.x0) / (p.x1 - p.x0))) * 2 * Math.PI,
						x1: Math.max(0, Math.min(1, (d.x1 - p.x0) / (p.x1 - p.x0))) * 2 * Math.PI,
						y0: Math.max(0, d.y0 - p.depth),
						y1: Math.max(0, d.y1 - p.depth)
					})
			);

			const t = g.transition().duration(750);

			path
				.transition(t as any)
				.tween('data', (d: any) => {
					const i = d3.interpolate(d.current, d.target);
					return (t: number) => (d.current = i(t));
				})
				.filter(function (d: any) {
					return !!(this as any).getAttribute('fill');
				})
				.attr('fill-opacity', (d: any) => (arcVisible(d.target) ? (d.children ? 0.6 : 0.4) : 0))
				.attrTween('d', (d: any) => () => arc(d.current));

			label
				.filter(function (d: any) {
					return !!(this as any).getAttribute('fill-opacity');
				})
				.transition(t as any)
				.attr('fill-opacity', (d: any) => +labelVisible(d.target))
				.attrTween('transform', (d: any) => () => labelTransform(d.current));
		}

		function arcVisible(d: any) {
			return d.y1 <= 3 && d.y0 >= 1 && d.x1 > d.x0;
		}

		function labelVisible(d: any) {
			return d.y1 <= 3 && d.y0 >= 1 && (d.y1 - d.y0) * (d.x1 - d.x0) > 0.03;
		}

		function labelTransform(d: any) {
			const x = (((d.x0 + d.x1) / 2) * 180) / Math.PI;
			const y = (d.y0 + d.y1) / 2;
			return `rotate(${x - 90}) translate(${y},0) rotate(${x < 180 ? 0 : 180})`;
		}

		// Add title
		svgSelection
			.append('text')
			.attr('x', width / 2)
			.attr('y', 20)
			.attr('text-anchor', 'middle')
			.style('font-size', '16px')
			.style('font-weight', 'bold')
			.text('Hierarchical Data Sunburst');

		// Add instruction
		svgSelection
			.append('text')
			.attr('x', width / 2)
			.attr('y', height - 10)
			.attr('text-anchor', 'middle')
			.style('font-size', '12px')
			.style('fill', '#666')
			.text('Click to zoom in/out');
	});

	// Redraw when data changes
	$: if (svg && data) {
		onMount();
	}
</script>

<div class="sunburst">
	<svg bind:this={svg} class="w-full"></svg>
</div>

<style>
	.sunburst {
		width: 100%;
		display: flex;
		justify-content: center;
	}
</style>

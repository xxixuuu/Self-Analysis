<script lang="ts">
	import { onMount } from 'svelte';
	import * as d3 from 'd3';

	export let data: {
		nodes: Array<{ id: string; group: string; value: number }>;
		links: Array<{ source: string; target: string; value: number }>;
	};
	export let width = 800;
	export let height = 600;

	let svg: SVGSVGElement;

	onMount(() => {
		if (!data || !data.nodes || !data.links) return;

		// Clear existing content
		d3.select(svg).selectAll('*').remove();

		// Create SVG
		const svgSelection = d3
			.select(svg)
			.attr('width', width)
			.attr('height', height)
			.attr('viewBox', [0, 0, width, height]);

		// Create force simulation
		const simulation = d3
			.forceSimulation(data.nodes as any)
			.force(
				'link',
				d3
					.forceLink(data.links)
					.id((d: any) => d.id)
					.distance(100)
			)
			.force('charge', d3.forceManyBody().strength(-300))
			.force('center', d3.forceCenter(width / 2, height / 2))
			.force('collision', d3.forceCollide().radius(30));

		// Color scale
		const color = d3.scaleOrdinal(d3.schemeCategory10);

		// Create links
		const link = svgSelection
			.append('g')
			.attr('class', 'links')
			.selectAll('line')
			.data(data.links)
			.join('line')
			.attr('stroke', '#999')
			.attr('stroke-opacity', 0.6)
			.attr('stroke-width', (d: any) => Math.sqrt(d.value));

		// Create nodes
		const node = svgSelection
			.append('g')
			.attr('class', 'nodes')
			.selectAll('circle')
			.data(data.nodes)
			.join('circle')
			.attr('r', (d: any) => Math.sqrt(d.value) * 3)
			.attr('fill', (d: any) => color(d.group))
			.call(drag(simulation) as any);

		// Add labels
		const label = svgSelection
			.append('g')
			.attr('class', 'labels')
			.selectAll('text')
			.data(data.nodes)
			.join('text')
			.text((d: any) => d.id)
			.attr('font-size', 10)
			.attr('dx', 12)
			.attr('dy', 4);

		// Add tooltips
		node.append('title').text((d: any) => `${d.id}\nValue: ${d.value}`);

		// Update positions on each tick
		simulation.on('tick', () => {
			link
				.attr('x1', (d: any) => d.source.x)
				.attr('y1', (d: any) => d.source.y)
				.attr('x2', (d: any) => d.target.x)
				.attr('y2', (d: any) => d.target.y);

			node.attr('cx', (d: any) => d.x).attr('cy', (d: any) => d.y);

			label.attr('x', (d: any) => d.x).attr('y', (d: any) => d.y);
		});

		// Drag behavior
		function drag(simulation: d3.Simulation<any, any>) {
			function dragstarted(event: any) {
				if (!event.active) simulation.alphaTarget(0.3).restart();
				event.subject.fx = event.subject.x;
				event.subject.fy = event.subject.y;
			}

			function dragged(event: any) {
				event.subject.fx = event.x;
				event.subject.fy = event.y;
			}

			function dragended(event: any) {
				if (!event.active) simulation.alphaTarget(0);
				event.subject.fx = null;
				event.subject.fy = null;
			}

			return d3.drag().on('start', dragstarted).on('drag', dragged).on('end', dragended);
		}
	});

	// Redraw when data changes
	$: if (svg && data) {
		onMount();
	}
</script>

<div class="network-graph">
	<svg bind:this={svg} class="w-full h-full"></svg>
</div>

<style>
	.network-graph {
		width: 100%;
		height: 100%;
	}
</style>

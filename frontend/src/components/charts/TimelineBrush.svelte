<script lang="ts">
	import { onMount } from 'svelte';
	import * as d3 from 'd3';

	export let data: Array<{ date: string; value: number }>;
	export let width = 900;
	export let height = 400;

	let svg: SVGSVGElement;

	onMount(() => {
		if (!data || data.length === 0) return;

		// Clear existing content
		d3.select(svg).selectAll('*').remove();

		// Parse dates
		const parseDate = d3.timeParse('%Y-%m-%d');
		const parsedData = data.map((d) => ({
			date: parseDate(d.date) || new Date(),
			value: d.value
		}));

		// Margins
		const margin = { top: 20, right: 20, bottom: 110, left: 50 };
		const margin2 = { top: 330, right: 20, bottom: 30, left: 50 };
		const innerWidth = width - margin.left - margin.right;
		const height1 = height - margin.top - margin.bottom - 100;
		const height2 = height - margin2.top - margin2.bottom;

		// Create SVG
		const svgSelection = d3
			.select(svg)
			.attr('width', width)
			.attr('height', height)
			.attr('viewBox', [0, 0, width, height]);

		// Clip path
		svgSelection
			.append('defs')
			.append('clipPath')
			.attr('id', 'clip')
			.append('rect')
			.attr('width', innerWidth)
			.attr('height', height1);

		// Scales for focus area
		const xScale = d3
			.scaleTime()
			.domain(d3.extent(parsedData, (d) => d.date) as [Date, Date])
			.range([0, innerWidth]);

		const yScale = d3
			.scaleLinear()
			.domain([0, d3.max(parsedData, (d) => d.value) || 1])
			.nice()
			.range([height1, 0]);

		// Scales for context area (brush)
		const xScale2 = d3
			.scaleTime()
			.domain(xScale.domain())
			.range([0, innerWidth]);

		const yScale2 = d3
			.scaleLinear()
			.domain(yScale.domain())
			.range([height2, 0]);

		// Area generator for focus
		const area = d3
			.area<{ date: Date; value: number }>()
			.curve(d3.curveMonotoneX)
			.x((d) => xScale(d.date))
			.y0(height1)
			.y1((d) => yScale(d.value));

		// Area generator for context
		const area2 = d3
			.area<{ date: Date; value: number }>()
			.curve(d3.curveMonotoneX)
			.x((d) => xScale2(d.date))
			.y0(height2)
			.y1((d) => yScale2(d.value));

		// Brush
		const brush = d3
			.brushX()
			.extent([
				[0, 0],
				[innerWidth, height2]
			])
			.on('brush end', brushed);

		// Focus group
		const focus = svgSelection
			.append('g')
			.attr('class', 'focus')
			.attr('transform', `translate(${margin.left},${margin.top})`);

		// Context group
		const context = svgSelection
			.append('g')
			.attr('class', 'context')
			.attr('transform', `translate(${margin2.left},${margin2.top})`);

		// Add area to focus
		focus
			.append('path')
			.datum(parsedData)
			.attr('class', 'area')
			.attr('d', area)
			.attr('fill', 'steelblue')
			.attr('clip-path', 'url(#clip)');

		// Add line to focus
		focus
			.append('path')
			.datum(parsedData)
			.attr('class', 'line')
			.attr(
				'd',
				d3
					.line<{ date: Date; value: number }>()
					.curve(d3.curveMonotoneX)
					.x((d) => xScale(d.date))
					.y((d) => yScale(d.value))
			)
			.attr('fill', 'none')
			.attr('stroke', 'steelblue')
			.attr('stroke-width', 1.5)
			.attr('clip-path', 'url(#clip)');

		// Add axes to focus
		const xAxis = d3.axisBottom(xScale);
		const yAxis = d3.axisLeft(yScale);

		focus
			.append('g')
			.attr('class', 'axis axis--x')
			.attr('transform', `translate(0,${height1})`)
			.call(xAxis);

		focus.append('g').attr('class', 'axis axis--y').call(yAxis);

		// Add area to context
		context
			.append('path')
			.datum(parsedData)
			.attr('class', 'area')
			.attr('d', area2)
			.attr('fill', 'steelblue')
			.attr('opacity', 0.5);

		// Add axis to context
		const xAxis2 = d3.axisBottom(xScale2);

		context
			.append('g')
			.attr('class', 'axis axis--x')
			.attr('transform', `translate(0,${height2})`)
			.call(xAxis2);

		// Add brush
		context.append('g').attr('class', 'brush').call(brush);

		// Brush event handler
		function brushed(event: any) {
			if (event.sourceEvent && event.sourceEvent.type === 'zoom') return;

			const selection = event.selection;
			if (selection) {
				xScale.domain(selection.map(xScale2.invert, xScale2));

				focus
					.select('.area')
					.attr('d', area as any);

				focus
					.select('.line')
					.attr(
						'd',
						d3
							.line<{ date: Date; value: number }>()
							.curve(d3.curveMonotoneX)
							.x((d) => xScale(d.date))
							.y((d) => yScale(d.value)) as any
					);

				focus.select('.axis--x').call(xAxis as any);
			}
		}

		// Add title
		svgSelection
			.append('text')
			.attr('x', width / 2)
			.attr('y', 15)
			.attr('text-anchor', 'middle')
			.style('font-size', '16px')
			.style('font-weight', 'bold')
			.text('Timeline with Brush');

		// Add Y axis label
		svgSelection
			.append('text')
			.attr('transform', 'rotate(-90)')
			.attr('x', -height / 2)
			.attr('y', 15)
			.attr('text-anchor', 'middle')
			.text('Value');
	});

	// Redraw when data changes
	$: if (svg && data) {
		onMount();
	}
</script>

<div class="timeline-brush">
	<svg bind:this={svg} class="w-full"></svg>
</div>

<style>
	.timeline-brush {
		width: 100%;
	}
</style>

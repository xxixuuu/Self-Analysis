/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {}
	},
	plugins: [require('daisyui')],
	daisyui: {
		themes: [
			{
				light: {
					primary: '#3b82f6',
					secondary: '#8b5cf6',
					accent: '#06b6d4',
					neutral: '#1f2937',
					'base-100': '#ffffff',
					info: '#0ea5e9',
					success: '#10b981',
					warning: '#f59e0b',
					error: '#ef4444'
				},
				dark: {
					primary: '#3b82f6',
					secondary: '#8b5cf6',
					accent: '#06b6d4',
					neutral: '#d1d5db',
					'base-100': '#1f2937',
					info: '#0ea5e9',
					success: '#10b981',
					warning: '#f59e0b',
					error: '#ef4444'
				}
			}
		],
		darkTheme: 'dark'
	}
};

/**
 * API client for backend communication.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export class APIClient {
	private baseUrl: string;
	private token: string | null = null;

	constructor(baseUrl: string = API_BASE_URL) {
		this.baseUrl = baseUrl;
		// Load token from localStorage if available
		if (typeof window !== 'undefined') {
			this.token = localStorage.getItem('access_token');
		}
	}

	setToken(token: string) {
		this.token = token;
		if (typeof window !== 'undefined') {
			localStorage.setItem('access_token', token);
		}
	}

	clearToken() {
		this.token = null;
		if (typeof window !== 'undefined') {
			localStorage.removeItem('access_token');
		}
	}

	private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
		const url = `${this.baseUrl}${endpoint}`;
		const headers: HeadersInit = {
			'Content-Type': 'application/json',
			...options.headers
		};

		if (this.token) {
			headers['Authorization'] = `Bearer ${this.token}`;
		}

		const response = await fetch(url, {
			...options,
			headers
		});

		if (!response.ok) {
			const error = await response.json().catch(() => ({ detail: response.statusText }));
			throw new Error(error.detail || 'API request failed');
		}

		return response.json();
	}

	// Auth endpoints
	async login(email: string, password: string) {
		const response = await this.request<{ access_token: string; token_type: string }>(
			'/api/auth/login',
			{
				method: 'POST',
				body: JSON.stringify({ email, password })
			}
		);
		this.setToken(response.access_token);
		return response;
	}

	async register(email: string, username: string, password: string) {
		return this.request('/api/auth/register', {
			method: 'POST',
			body: JSON.stringify({ email, username, password })
		});
	}

	async getCurrentUser() {
		return this.request('/api/auth/me');
	}

	// Dashboard endpoints
	async getDashboardStats() {
		return this.request('/api/dashboard/stats');
	}

	async getDashboardData(period: string = 'week') {
		return this.request(`/api/dashboard/data?period=${period}`);
	}

	async getActivities(limit: number = 50, offset: number = 0) {
		return this.request(`/api/dashboard/activities?limit=${limit}&offset=${offset}`);
	}

	async getProductivityScores(days: number = 30) {
		return this.request(`/api/dashboard/productivity?days=${days}`);
	}

	// Insights endpoints
	async getInsights(limit: number = 20, type?: string) {
		const params = new URLSearchParams({ limit: limit.toString() });
		if (type) params.append('insight_type', type);
		return this.request(`/api/insights?${params}`);
	}

	async generateDailySummary(date?: string) {
		const params = date ? `?date=${date}` : '';
		return this.request(`/api/insights/generate-daily-summary${params}`, {
			method: 'POST'
		});
	}

	async query(question: string) {
		return this.request('/api/insights/query', {
			method: 'POST',
			body: JSON.stringify({ query: question })
		});
	}

	async analyzeProductivity(days: number = 7) {
		return this.request(`/api/insights/analyze-productivity?days=${days}`, {
			method: 'POST'
		});
	}
}

export const api = new APIClient();

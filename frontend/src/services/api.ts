import type { DashboardMetrics, Payment, AuditLog, AnalysisResponse, RecoveryResponse } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers = {
    'Content-Type': 'application/json',
    ...(options?.headers || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP Error ${response.status}: ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  getAnalytics: () => request<DashboardMetrics>('/analytics'),
  
  getPayments: (status?: string, search?: string) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (search) params.append('search', search);
    const queryString = params.toString() ? `?${params.toString()}` : '';
    return request<Payment[]>(`/payments${queryString}`);
  },
  
  getPaymentDetails: (id: string) => request<Payment>(`/payments/${id}`),
  
  getAuditTrail: (id: string) => request<AuditLog[]>(`/payments/${id}/audit`),
  
  analyzePayment: (id: string) => request<AnalysisResponse>(`/payments/${id}/analyze`, {
    method: 'POST',
  }),
  
  recoverPayment: (id: string) => request<RecoveryResponse>(`/payments/${id}/recover`, {
    method: 'POST',
  }),
  
  seedDemoData: (nPayments: number = 150) => request<{ success: boolean; message: string }>(`/demo/seed?n_payments=${nPayments}`, {
    method: 'POST',
  }),
  
  simulateFailure: () => request<any>('/demo/simulate_failure', {
    method: 'POST',
  }),
};

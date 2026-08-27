import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  AlertTriangle, 
  ArrowLeft, 
  CheckCircle, 
  Clock, 
  Database, 
  DollarSign, 
  Eye, 
  HelpCircle, 
  Info, 
  Play, 
  RefreshCw, 
  Search, 
  ShieldCheck, 
  TrendingUp, 
  XCircle 
} from 'lucide-react';
import { api } from './services/api';
import type { Payment, DashboardMetrics, AuditLog } from './types';

export default function App() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [selectedPayment, setSelectedPayment] = useState<Payment | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  
  // Navigation
  const [currentPage, setCurrentPage] = useState<'dashboard' | 'detail'>('dashboard');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  
  // Loading & Action states
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // Load dashboard data
  const loadDashboardData = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const [analyticsData, paymentsData] = await Promise.all([
        api.getAnalytics(),
        api.getPayments(filterStatus, searchQuery)
      ]);
      setMetrics(analyticsData);
      setPayments(paymentsData);
      
      // If we are currently viewing details, refresh the selected payment too
      if (selectedPayment) {
        const updatedPayment = await api.getPaymentDetails(selectedPayment.id);
        setSelectedPayment(updatedPayment);
        const updatedLogs = await api.getAuditTrail(selectedPayment.id);
        setAuditLogs(updatedLogs);
      }
    } catch (err: any) {
      console.error(err);
      showToast(err.message || 'Error loading dashboard data', 'error');
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [filterStatus]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadDashboardData(false);
  };

  const showToast = (text: string, type: 'success' | 'error') => {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 4000);
  };

  // Seed DB with mock data
  const handleSeedData = async () => {
    setActionLoading('seed');
    try {
      const res = await api.seedDemoData(150);
      showToast(res.message, 'success');
      await loadDashboardData();
    } catch (err: any) {
      showToast(err.message || 'Failed to seed database', 'error');
    } finally {
      setActionLoading(null);
    }
  };

  // Simulate checkout failure with automatic recovery
  const handleSimulateCheckoutFailure = async () => {
    setActionLoading('simulate');
    try {
      const res = await api.simulateFailure();
      showToast(
        `Captured failed checkout of ₹${res.amount} for ${res.customer}. AI recovered payment automatically! (Status: ${res.recovery_status})`,
        'success'
      );
      await loadDashboardData(false);
    } catch (err: any) {
      showToast(err.message || 'Simulation failed', 'error');
    } finally {
      setActionLoading(null);
    }
  };

  // Run AI analysis
  const handleRunAnalysis = async (paymentId: string) => {
    setActionLoading('analyze');
    try {
      const res = await api.analyzePayment(paymentId);
      showToast(`AI Analysis generated strategy: ${res.ai_decision} (Policy: ${res.policy_result})`, 'success');
      
      // Refresh current details
      const updatedPayment = await api.getPaymentDetails(paymentId);
      setSelectedPayment(updatedPayment);
      const updatedLogs = await api.getAuditTrail(paymentId);
      setAuditLogs(updatedLogs);
      
      // Refresh background dashboard statistics
      await api.getAnalytics().then(setMetrics);
    } catch (err: any) {
      showToast(err.message || 'Failed to analyze payment', 'error');
    } finally {
      setActionLoading(null);
    }
  };

  // Execute recovery action
  const handleExecuteRecovery = async (paymentId: string) => {
    setActionLoading('recover');
    try {
      const res = await api.recoverPayment(paymentId);
      if (res.success) {
        showToast(res.message, 'success');
      } else {
        showToast(res.message, 'error');
      }
      
      // Refresh current details
      const updatedPayment = await api.getPaymentDetails(paymentId);
      setSelectedPayment(updatedPayment);
      const updatedLogs = await api.getAuditTrail(paymentId);
      setAuditLogs(updatedLogs);
      
      // Refresh background dashboard statistics
      await api.getAnalytics().then(setMetrics);
    } catch (err: any) {
      showToast(err.message || 'Failed to execute recovery', 'error');
    } finally {
      setActionLoading(null);
    }
  };

  // Navigate to payment details
  const viewPaymentDetails = async (payment: Payment) => {
    setLoading(true);
    try {
      const fullPayment = await api.getPaymentDetails(payment.id);
      const logs = await api.getAuditTrail(payment.id);
      setSelectedPayment(fullPayment);
      setAuditLogs(logs);
      setCurrentPage('detail');
    } catch (err: any) {
      showToast(err.message || 'Failed to load details', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Map failure categories to UI colors and badges
  const getCategoryBadgeColor = (category: string | null) => {
    if (!category) return 'bg-gray-500/10 text-gray-400 border-gray-500/20';
    switch (category) {
      case 'TEMPORARY_BANK_FAILURE':
      case 'NETWORK_FAILURE':
      case 'TIMEOUT':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'INSUFFICIENT_FUNDS':
      case 'CUSTOMER_ACTION_REQUIRED':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'EXPIRED_CARD':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
      case 'INVALID_CARD':
      case 'PERMANENT_FAILURE':
      case 'DUPLICATE_PAYMENT':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
    }
  };

  // Map statuses to UI badges
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">SUCCESS</span>;
      case 'RECOVERED':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 glow-emerald animate-pulse">RECOVERED</span>;
      case 'FAILED':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">FAILED</span>;
      case 'RECOVERING':
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 animate-pulse">RECOVERING</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-xs font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/20">{status}</span>;
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a16] text-slate-100 flex flex-col antialiased">
      {/* Toast Alert */}
      {message && (
        <div className={`fixed top-5 right-5 z-50 px-4 py-3 rounded-lg shadow-xl flex items-center gap-2 border transition-all duration-300 transform translate-y-0 ${
          message.type === 'success' 
            ? 'bg-emerald-950/90 text-emerald-200 border-emerald-800 glow-emerald' 
            : 'bg-rose-950/90 text-rose-200 border-rose-800'
        }`}>
          {message.type === 'success' ? <CheckCircle size={18} /> : <AlertTriangle size={18} />}
          <span className="text-sm font-medium">{message.text}</span>
        </div>
      )}

      {/* Premium Tech Header */}
      <header className="border-b border-slate-800 bg-[#0d0e1f] px-6 py-4 flex items-center justify-between sticky top-0 z-40 backdrop-blur-md bg-opacity-95">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-indigo-600 flex items-center justify-center glow-indigo">
            <Activity size={22} className="text-white animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-1.5">
              RazorRecover <span className="text-xs px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">AI Agent</span>
            </h1>
            <p className="text-[10px] text-slate-500 tracking-wider uppercase font-semibold">Autonomous Revenue Protection</p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="hidden md:flex items-center gap-4 text-xs font-medium text-slate-400">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
              <span>AI Policy Engine: <strong className="text-white">Active</strong></span>
            </div>
            <div className="w-1.5 h-1.5 rounded-full bg-slate-700"></div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span>Razorpay Sandbox: <strong className="text-white">Connected</strong></span>
            </div>
          </div>

          <button 
            onClick={handleSeedData}
            disabled={actionLoading !== null}
            className="flex items-center gap-2 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 hover:border-slate-600 transition disabled:opacity-50"
          >
            <Database size={14} className={actionLoading === 'seed' ? 'animate-spin' : ''} />
            Reset & Seed Demo Data
          </button>
        </div>
      </header>

      {/* Main Workspace */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
        {loading && currentPage === 'dashboard' && payments.length === 0 ? (
          <div className="h-96 flex flex-col items-center justify-center gap-3">
            <RefreshCw className="animate-spin text-indigo-500" size={32} />
            <p className="text-sm text-slate-400">Querying transaction database and metrics...</p>
          </div>
        ) : currentPage === 'dashboard' ? (
          // ==================== DASHBOARD PAGE ====================
          <div className="space-y-6">
            
            {/* Metric Grid */}
            {metrics && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                
                <div className="glass-card p-5 rounded-xl flex flex-col justify-between hover:border-indigo-500/20 transition duration-300">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Failed Transactions</span>
                    <AlertTriangle className="text-rose-400" size={18} />
                  </div>
                  <div className="mt-4">
                    <h3 className="text-2xl font-bold text-white">{metrics.failed_transactions}</h3>
                    <p className="text-xs text-slate-500 mt-1">out of {metrics.total_transactions} total payments</p>
                  </div>
                </div>

                <div className="glass-card p-5 rounded-xl flex flex-col justify-between hover:border-indigo-500/20 transition duration-300">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Revenue at Risk</span>
                    <DollarSign className="text-rose-400" size={18} />
                  </div>
                  <div className="mt-4">
                    <h3 className="text-2xl font-bold text-white">₹{metrics.revenue_at_risk.toLocaleString('en-IN')}</h3>
                    <p className="text-xs text-slate-500 mt-1">potential loss from failures</p>
                  </div>
                </div>

                <div className="glass-card p-5 rounded-xl flex flex-col justify-between hover:border-emerald-500/20 transition duration-300 glow-indigo">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wide">Revenue Recovered</span>
                    <DollarSign className="text-emerald-400" size={18} />
                  </div>
                  <div className="mt-4">
                    <h3 className="text-2xl font-bold text-emerald-400">₹{metrics.revenue_recovered.toLocaleString('en-IN')}</h3>
                    <p className="text-xs text-emerald-500/80 font-medium flex items-center gap-1 mt-1">
                      <TrendingUp size={12} />
                      ₹{metrics.revenue_remaining_at_risk.toLocaleString('en-IN')} remaining risk
                    </p>
                  </div>
                </div>

                <div className="glass-card p-5 rounded-xl flex flex-col justify-between hover:border-indigo-500/20 transition duration-300">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Recovery Rate</span>
                    <ShieldCheck className="text-indigo-400" size={18} />
                  </div>
                  <div className="mt-4 flex items-end justify-between">
                    <div>
                      <h3 className="text-3xl font-bold text-white">{metrics.recovery_rate}%</h3>
                      <p className="text-[10px] text-slate-500 mt-1">{metrics.successful_recoveries} successful retries</p>
                    </div>
                    {/* Ring indicator */}
                    <div className="relative w-12 h-12 flex items-center justify-center">
                      <svg className="w-full h-full transform -rotate-90">
                        <circle cx="24" cy="24" r="20" fill="transparent" stroke="#1f2937" strokeWidth="4" />
                        <circle cx="24" cy="24" r="20" fill="transparent" stroke="#6366f1" strokeWidth="4" 
                          strokeDasharray={125.6} 
                          strokeDashoffset={125.6 - (125.6 * metrics.recovery_rate) / 100} 
                        />
                      </svg>
                      <span className="absolute text-[10px] font-bold">{Math.round(metrics.recovery_rate)}%</span>
                    </div>
                  </div>
                </div>

              </div>
            )}

            {/* Quick Demo Actions & Scenario Guide */}
            <div className="glass-card p-5 rounded-xl border-dashed border-slate-700">
              <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold text-white flex items-center gap-2">
                    <Info size={16} className="text-indigo-400" />
                    Fintech Hackathon Evaluation Mode
                  </h4>
                  <p className="text-xs text-slate-400 max-w-3xl">
                    To demonstrate the full autonomous loop, select the pre-loaded <strong>Transaction #pay_demo_123</strong> (Temporary Bank Failure) in the payment list below. Click it to trigger the ML probability model, evaluate against the policy guardrails, run the AI agent planning flow, and execute the sandbox recovery action.
                  </p>
                </div>
                <div className="flex flex-col sm:flex-row gap-2 w-full md:w-auto">
                  <button 
                    onClick={() => {
                      const pay = payments.find(p => p.id === 'pay_demo_123');
                      if (pay) viewPaymentDetails(pay);
                      else showToast("Transaction #pay_demo_123 not loaded. Click 'Reset & Seed Demo Data' first.", 'error');
                    }}
                    className="px-4 py-2 rounded bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white tracking-wide uppercase transition glow-indigo flex items-center justify-center gap-1.5 whitespace-nowrap"
                  >
                    <Play size={14} fill="white" />
                    Launch Judge Demo
                  </button>
                  
                  <button 
                    onClick={handleSimulateCheckoutFailure}
                    disabled={actionLoading !== null}
                    className="px-4 py-2 rounded bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white tracking-wide uppercase transition glow-emerald flex items-center justify-center gap-1.5 whitespace-nowrap disabled:opacity-50"
                  >
                    <Activity size={14} className={actionLoading === 'simulate' ? 'animate-spin' : ''} />
                    Simulate Auto-Recovery checkout
                  </button>
                </div>
              </div>
            </div>

            {/* Filter and Table Grid */}
            <div className="glass-card rounded-xl overflow-hidden">
              {/* Table header with Search/Filter */}
              <div className="p-4 border-b border-slate-800 bg-[#0d0e1f]/50 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-white text-sm">Payment Attempts Audit Ledger</h3>
                  <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-slate-800 text-slate-400">{payments.length} items</span>
                </div>

                <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 w-full sm:w-auto">
                  {/* Status filter */}
                  <select 
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className="bg-slate-900 border border-slate-800 rounded px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="">All Statuses</option>
                    <option value="SUCCESS">SUCCESS</option>
                    <option value="FAILED">FAILED</option>
                    <option value="RECOVERING">RECOVERING</option>
                    <option value="RECOVERED">RECOVERED</option>
                  </select>

                  {/* Search input */}
                  <div className="relative flex-1 sm:flex-initial">
                    <input 
                      type="text" 
                      placeholder="Search ID, email..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="bg-slate-900 border border-slate-800 rounded pl-8 pr-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-indigo-500 placeholder-slate-600 w-full"
                    />
                    <Search size={14} className="absolute left-2.5 top-2.5 text-slate-600" />
                  </div>
                  
                  <button type="submit" className="hidden" />
                </form>
              </div>

              {/* Payments Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 bg-slate-950/20 text-slate-400 font-semibold uppercase tracking-wider">
                      <th className="p-4">Transaction ID</th>
                      <th className="p-4">Customer</th>
                      <th className="p-4 text-right">Amount</th>
                      <th className="p-4">Method</th>
                      <th className="p-4">Failure Category</th>
                      <th className="p-4">Status</th>
                      <th className="p-4">Retries</th>
                      <th className="p-4 text-center">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {payments.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="p-8 text-center text-slate-500 text-sm">
                          No transaction records found. Click <strong>Reset & Seed Demo Data</strong> to load datasets.
                        </td>
                      </tr>
                    ) : (
                      payments.map((pay) => (
                        <tr key={pay.id} className="hover:bg-slate-800/10 transition duration-150">
                          <td className="p-4 font-mono font-bold text-white flex items-center gap-1.5">
                            {pay.id === 'pay_demo_123' && <span className="w-2 h-2 rounded-full bg-indigo-500 animate-ping"></span>}
                            {pay.id}
                          </td>
                          <td className="p-4">
                            <div className="font-semibold text-slate-200">{pay.customer.customer_reference}</div>
                            <div className="text-[10px] text-slate-500">{pay.customer.email || 'No Email'}</div>
                          </td>
                          <td className="p-4 text-right font-bold text-white">₹{pay.amount.toLocaleString('en-IN')}</td>
                          <td className="p-4 font-medium uppercase text-slate-400">{pay.payment_method}</td>
                          <td className="p-4">
                            {pay.failure_category ? (
                              <span className={`px-2 py-0.5 rounded border text-[10px] font-semibold ${getCategoryBadgeColor(pay.failure_category)}`}>
                                {pay.failure_category.replace(/_/g, ' ')}
                              </span>
                            ) : (
                              <span className="text-slate-600">-</span>
                            )}
                          </td>
                          <td className="p-4">{getStatusBadge(pay.status)}</td>
                          <td className="p-4 text-slate-400 font-medium">{pay.retry_count} / 3</td>
                          <td className="p-4 text-center">
                            <button 
                              onClick={() => viewPaymentDetails(pay)}
                              className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white font-semibold transition border border-slate-700 flex items-center gap-1 mx-auto"
                            >
                              <Eye size={12} />
                              Analyze
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        ) : (
          // ==================== DETAILS PAGE ====================
          selectedPayment && (
            <div className="space-y-6">
              
              {/* Back Button and title */}
              <div className="flex items-center justify-between">
                <button 
                  onClick={() => {
                    setCurrentPage('dashboard');
                    loadDashboardData(false);
                  }}
                  className="flex items-center gap-2 px-3 py-1.5 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white text-xs font-semibold transition"
                >
                  <ArrowLeft size={14} />
                  Back to Dashboard
                </button>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500 font-medium">Transaction Reference:</span>
                  <span className="font-mono text-sm font-bold text-white bg-slate-900 border border-slate-800 px-3 py-1 rounded">{selectedPayment.id}</span>
                </div>
              </div>

              {/* Top Summary Banner */}
              <div className="glass-card rounded-xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <h2 className="text-2xl font-bold text-white">₹{selectedPayment.amount.toLocaleString('en-IN')}</h2>
                    {getStatusBadge(selectedPayment.status)}
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-1.5 text-xs">
                    <div className="text-slate-500">Method: <strong className="text-slate-300 uppercase">{selectedPayment.payment_method}</strong></div>
                    <div className="text-slate-500">Customer: <strong className="text-slate-300">{selectedPayment.customer.customer_reference}</strong></div>
                    <div className="text-slate-500">Email: <strong className="text-slate-300">{selectedPayment.customer.email || '-'}</strong></div>
                    <div className="text-slate-500">Phone: <strong className="text-slate-300">{selectedPayment.customer.phone || '-'}</strong></div>
                  </div>
                </div>
                
                {/* Razorpay transaction id link */}
                <div className="text-xs text-slate-400 md:text-right space-y-1">
                  <div>Gateway: <strong>Razorpay TEST/SANDBOX</strong></div>
                  <div>Razorpay Payment ID: <span className="font-mono text-white bg-slate-950 px-2 py-0.5 rounded text-[11px] font-bold">{selectedPayment.razorpay_payment_id || 'N/A'}</span></div>
                </div>
              </div>

              {/* Core Execution Panels */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Panel 1: Failure Classification and ML Score */}
                <div className="glass-card rounded-xl p-6 flex flex-col justify-between space-y-6">
                  <div>
                    <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-800 pb-3">
                      <AlertTriangle size={16} className="text-rose-400" />
                      1. Payment Failure Analysis
                    </h3>
                    
                    <div className="mt-4 space-y-4">
                      <div>
                        <span className="text-[10px] text-slate-500 uppercase font-semibold">Gateway Error Code</span>
                        <p className="font-mono text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2 py-1.5 rounded mt-1 font-bold">
                          {selectedPayment.failure_code || 'N/A'}
                        </p>
                      </div>

                      <div>
                        <span className="text-[10px] text-slate-500 uppercase font-semibold">Raw Failure Reason</span>
                        <p className="text-xs text-slate-300 leading-relaxed bg-slate-900 p-2.5 rounded border border-slate-800 mt-1">
                          {selectedPayment.failure_reason || 'Unknown checkout drop-off.'}
                        </p>
                      </div>

                      <div>
                        <span className="text-[10px] text-slate-500 uppercase font-semibold">AI Classified Category</span>
                        <div className="mt-1">
                          <span className={`px-2.5 py-1 rounded border text-xs font-semibold ${getCategoryBadgeColor(selectedPayment.failure_category)}`}>
                            {selectedPayment.failure_category ? selectedPayment.failure_category.replace(/_/g, ' ') : 'UNCLASSIFIED'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* ML model prediction gauge */}
                  <div className="bg-[#0f1020]/80 p-4 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-indigo-400 uppercase font-bold tracking-wider">ML Prediction Score</span>
                    
                    {selectedPayment.decisions.length > 0 ? (
                      <div className="mt-3 flex items-center justify-between">
                        <div>
                          <h4 className="text-2xl font-bold text-white">{Math.round(selectedPayment.decisions[0].confidence * 100)}%</h4>
                          <p className="text-[10px] text-slate-500 mt-0.5">Recovery Probability</p>
                        </div>
                        <div className="relative w-14 h-14 flex items-center justify-center">
                          <svg className="w-full h-full transform -rotate-90">
                            <circle cx="28" cy="28" r="24" fill="transparent" stroke="#1c1d33" strokeWidth="4" />
                            <circle cx="28" cy="28" r="24" fill="transparent" stroke={selectedPayment.decisions[0].confidence >= 0.75 ? '#10b981' : '#f59e0b'} strokeWidth="4" 
                              strokeDasharray={150.7} 
                              strokeDashoffset={150.7 - (150.7 * selectedPayment.decisions[0].confidence)} 
                            />
                          </svg>
                          <span className="absolute text-[10px] font-bold text-white">
                            {selectedPayment.decisions[0].confidence >= 0.75 ? 'HIGH' : 'MED'}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <p className="text-xs text-slate-500 mt-2 italic flex items-center gap-1">
                        <Info size={12} />
                        Run AI Analysis to compute probability.
                      </p>
                    )}
                  </div>

                </div>

                {/* Panel 2: AI Recommendation & Policy Gate */}
                <div className="glass-card rounded-xl p-6 flex flex-col justify-between space-y-6">
                  <div>
                    <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-800 pb-3">
                      <Activity size={16} className="text-indigo-400" />
                      2. AI Plan & Policy Check
                    </h3>

                    {selectedPayment.decisions.length > 0 ? (
                      <div className="mt-4 space-y-4">
                        <div>
                          <span className="text-[10px] text-slate-500 uppercase font-semibold">Recommended AI Strategy</span>
                          <div className="flex items-center gap-2 mt-1.5">
                            <span className="px-3 py-1 rounded-md text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                              {selectedPayment.decisions[0].decision}
                            </span>
                          </div>
                        </div>

                        {/* Policy check result */}
                        <div>
                          <span className="text-[10px] text-slate-500 uppercase font-semibold">Policy Engine Validation</span>
                          <div className="mt-1.5 flex items-center gap-1.5">
                            {selectedPayment.decisions[0].policy_result === 'APPROVED' ? (
                              <>
                                <CheckCircle size={14} className="text-emerald-400" />
                                <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">APPROVED BY POLICY</span>
                              </>
                            ) : (
                              <>
                                <XCircle size={14} className="text-rose-400" />
                                <span className="text-xs font-bold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded">BLOCKED BY POLICY</span>
                              </>
                            )}
                          </div>
                        </div>

                        {/* Rationale explanation text */}
                        <div>
                          <span className="text-[10px] text-slate-500 uppercase font-semibold">Decision Explanation</span>
                          <div className="text-xs text-slate-300 italic leading-relaxed bg-[#141527] border border-slate-800/80 p-3 rounded-lg mt-1.5">
                            "{selectedPayment.decisions[0].explanation}"
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="mt-8 text-center space-y-3">
                        <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-slate-500">
                          <HelpCircle size={20} />
                        </div>
                        <p className="text-xs text-slate-500 max-w-[200px] mx-auto italic">
                          Click <strong>Analyze Transaction</strong> below to load AI Agent recommendation context.
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Actions buttons */}
                  <div className="space-y-2 pt-4 border-t border-slate-800/60">
                    <button 
                      onClick={() => handleRunAnalysis(selectedPayment.id)}
                      disabled={actionLoading !== null || selectedPayment.status === 'RECOVERED'}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 hover:border-slate-600 transition disabled:opacity-50"
                    >
                      <Activity size={14} className={actionLoading === 'analyze' ? 'animate-spin' : ''} />
                      Analyze Transaction
                    </button>
                    
                    <button 
                      onClick={() => handleExecuteRecovery(selectedPayment.id)}
                      disabled={
                        actionLoading !== null || 
                        selectedPayment.decisions.length === 0 || 
                        selectedPayment.decisions[0].policy_result !== 'APPROVED' ||
                        selectedPayment.status === 'RECOVERED'
                      }
                      className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white tracking-wide uppercase transition disabled:opacity-50 glow-indigo"
                    >
                      <Play size={14} className={actionLoading === 'recover' ? 'animate-spin' : ''} />
                      Execute Recovery
                    </button>
                  </div>

                </div>

                {/* Panel 3: Chronological Audit Trail Timeline */}
                <div className="glass-card rounded-xl p-6 flex flex-col">
                  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 border-b border-slate-800 pb-3">
                    <Clock size={16} className="text-indigo-400" />
                    3. Immutability Ledger Audit Trail
                  </h3>

                  <div className="flex-1 mt-4 space-y-4 overflow-y-auto max-h-[340px] pr-1">
                    {auditLogs.length === 0 ? (
                      <p className="text-xs text-slate-500 italic mt-2">No audit logs recorded.</p>
                    ) : (
                      auditLogs.map((log, idx) => (
                        <div key={log.id} className="relative flex gap-3 pb-4">
                          {/* Vertical timeline line */}
                          {idx < auditLogs.length - 1 && (
                            <span className="absolute left-[9px] top-4 bottom-0 w-[2px] bg-slate-800" />
                          )}
                          
                          {/* Timeline dot */}
                          <div className={`w-5 h-5 rounded-full flex items-center justify-center border z-10 ${
                            log.action.includes('SUCCEEDED') 
                              ? 'bg-emerald-950 border-emerald-500 text-emerald-400' 
                              : log.action.includes('BLOCKED') || log.action.includes('FAILED')
                              ? 'bg-rose-950 border-rose-500 text-rose-400'
                              : 'bg-slate-900 border-slate-700 text-indigo-400'
                          }`}>
                            <span className="w-1.5 h-1.5 rounded-full bg-current" />
                          </div>

                          {/* Log content */}
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <h4 className="text-xs font-bold text-white tracking-wide">{log.action.replace(/_/g, ' ')}</h4>
                              <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-800/80 text-slate-400 font-semibold border border-slate-700">{log.actor}</span>
                            </div>
                            <p className="text-[11px] text-slate-400 leading-relaxed">{log.reason}</p>
                            <span className="text-[9px] text-slate-600 block">{new Date(log.timestamp).toLocaleTimeString()}</span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>

              </div>

            </div>
          )
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/40 py-6 px-6 text-center text-xs text-slate-600">
        <p>© 2026 RazorRecover AI. Built for the Razorpay Buildathon. Simulated Sandbox Sandbox Mode.</p>
      </footer>
    </div>
  );
}

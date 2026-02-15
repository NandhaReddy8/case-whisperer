import { LegalCase, SearchFormData, CaseHistory } from '@/types/case';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface CaseSearchRequest {
  search_type: 'cnr' | 'case' | 'diary' | 'party' | 'filing';
  cnr_number?: string;
  case_type?: string;
  case_number?: string;
  year?: string;
  diary_number?: string;
  filing_number?: string;
  party_name?: string;
  court_state_code?: string;
  court_code?: string;
}

export interface CaseCreateRequest {
  search_request: CaseSearchRequest;
  sync_calendar?: boolean;
}

export interface CaseUpdateRequest {
  sync_calendar?: boolean;
  current_status?: string;
  next_hearing_date?: string;
}

export interface RefreshRequest {
  case_id: number;
  force_refresh?: boolean;
}

export interface BulkRefreshRequest {
  case_ids?: number[];
  force_refresh?: boolean;
}

export interface Court {
  state_code: string;
  court_code?: string;
  name: string;
}

export interface CaseType {
  code: string;
  description: string;
}

export interface ActType {
  code: string;
  description: string;
}

export interface CaseStats {
  total_cases: number;
  pending_cases: number;
  disposed_cases: number;
  storage_stats: {
    cases: number;
    case_types: number;
    act_types: number;
    courts: number;
  };
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      return { 
        error: error instanceof Error ? error.message : 'Unknown error occurred' 
      };
    }
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string; timestamp: string }>> {
    return this.request('/health');
  }

  // Case management
  async getCases(
    skip: number = 0, 
    limit: number = 100, 
    statusFilter?: string
  ): Promise<ApiResponse<LegalCase[]>> {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    });
    
    if (statusFilter) {
      params.append('status_filter', statusFilter);
    }
    
    return this.request(`/cases?${params.toString()}`);
  }

  async searchCases(query: string, field: string = 'petitioner'): Promise<ApiResponse<LegalCase[]>> {
    const params = new URLSearchParams({
      query,
      field,
    });
    
    return this.request(`/cases/search?${params.toString()}`);
  }

  async getCase(caseId: number): Promise<ApiResponse<LegalCase>> {
    return this.request(`/cases/${caseId}`);
  }

  async addCase(caseData: CaseCreateRequest): Promise<ApiResponse<LegalCase>> {
    return this.request('/cases', {
      method: 'POST',
      body: JSON.stringify(caseData),
    });
  }

  async updateCase(caseId: number, updates: CaseUpdateRequest): Promise<ApiResponse<LegalCase>> {
    return this.request(`/cases/${caseId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteCase(caseId: number): Promise<ApiResponse<{ message: string }>> {
    return this.request(`/cases/${caseId}`, {
      method: 'DELETE',
    });
  }

  // Case refresh
  async refreshCase(caseId: number, forceRefresh: boolean = false): Promise<ApiResponse<LegalCase>> {
    return this.request(`/cases/${caseId}/refresh`, {
      method: 'POST',
      body: JSON.stringify({
        case_id: caseId,
        force_refresh: forceRefresh,
      }),
    });
  }

  async bulkRefreshCases(request: BulkRefreshRequest): Promise<ApiResponse<{ 
    message: string;
    stats: {
      total: number;
      updated: number;
      failed: number;
      unchanged: number;
    };
  }>> {
    return this.request('/cases/refresh/bulk', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getRefreshStatus(): Promise<ApiResponse<{
    scheduler_running: boolean;
    scheduler_enabled: boolean;
    storage_stats: any;
    last_refresh: string;
  }>> {
    return this.request('/cases/refresh/status');
  }

  // Case search (without adding)
  async searchCase(searchRequest: CaseSearchRequest): Promise<ApiResponse<{
    found: boolean;
    case_data?: any;
    preview?: {
      cnr_number: string;
      case_type: string;
      registration_number: string;
      petitioner: string;
      respondent: string;
    };
    message?: string;
  }>> {
    return this.request('/cases/search', {
      method: 'POST',
      body: JSON.stringify(searchRequest),
    });
  }

  // Enhanced court and case type management
  async getCourts(): Promise<ApiResponse<{ courts: Court[] }>> {
    return this.request('/courts');
  }

  async getCaseTypes(stateCode: string, courtCode?: string): Promise<ApiResponse<{ case_types: CaseType[] }>> {
    const params = new URLSearchParams();
    if (courtCode) {
      params.append('court_code', courtCode);
    }
    
    const queryString = params.toString();
    const endpoint = `/courts/${stateCode}/case-types${queryString ? `?${queryString}` : ''}`;
    
    return this.request(endpoint);
  }

  async getActTypes(stateCode: string, courtCode?: string, query: string = ''): Promise<ApiResponse<{ act_types: ActType[] }>> {
    const params = new URLSearchParams();
    if (courtCode) {
      params.append('court_code', courtCode);
    }
    if (query) {
      params.append('query', query);
    }
    
    const queryString = params.toString();
    const endpoint = `/courts/${stateCode}/act-types${queryString ? `?${queryString}` : ''}`;
    
    return this.request(endpoint);
  }

  // Statistics and analytics
  async getCaseStats(): Promise<ApiResponse<CaseStats>> {
    return this.request('/cases/stats');
  }

  // Export functionality
  async exportCases(format: 'json' | 'csv' = 'json'): Promise<ApiResponse<any>> {
    return this.request(`/cases/export?format=${format}`, {
      method: 'POST',
    });
  }

  // Helper method to convert frontend SearchFormData to backend CaseSearchRequest
  convertSearchFormData(formData: SearchFormData): CaseSearchRequest {
    const request: CaseSearchRequest = {
      search_type: formData.searchType,
      court_state_code: formData.courtStateCode || '6', // Default to Gujarat
      court_code: formData.courtCode,
    };

    switch (formData.searchType) {
      case 'cnr':
        request.cnr_number = formData.cnrNumber;
        break;
      case 'case':
        request.case_type = formData.caseType;
        request.case_number = formData.caseNumber;
        request.year = formData.year;
        break;
      case 'diary':
        request.diary_number = formData.diaryNumber;
        request.year = formData.year;
        break;
      case 'filing':
        request.filing_number = formData.filingNumber;
        request.year = formData.year;
        break;
      case 'party':
        request.party_name = formData.partyName;
        break;
    }

    return request;
  }

  // Helper method to convert backend case data to frontend LegalCase
  convertToLegalCase(backendCase: any): LegalCase {
    return {
      id: backendCase.id.toString(),
      caseNo: backendCase.case_number || backendCase.cnr_number,
      cnrNumber: backendCase.cnr_number,
      caseType: backendCase.case_type || 'Unknown',
      petitioner: backendCase.petitioner || 'Unknown',
      respondent: backendCase.respondent || 'Unknown',
      courtName: backendCase.court_name || 'Unknown Court',
      nextHearingDate: backendCase.next_hearing_date,
      status: this.mapStatus(backendCase.current_status),
      filingDate: backendCase.filing_date || backendCase.created_at,
      advocates: backendCase.advocates || {
        petitioner: 'Not available',
        respondent: 'Not available',
      },
      history: this.convertHistory(backendCase.case_data?.hearings || []),
      syncCalendar: backendCase.sync_calendar || false,
      lastSyncedAt: backendCase.last_synced_at,
      // Enhanced fields from reference implementation
      registrationNumber: backendCase.registration_number,
      registrationDate: backendCase.registration_date,
      firstHearingDate: backendCase.first_hearing_date,
      decisionDate: backendCase.decision_date,
      natureOfDisposal: backendCase.nature_of_disposal,
      coram: backendCase.coram,
      bench: backendCase.bench,
      category: backendCase.category,
      subCategory: backendCase.sub_category,
    };
  }

  private mapStatus(status?: string): 'pending' | 'disposed' | 'reserved' {
    if (!status) return 'pending';
    
    const lowerStatus = status.toLowerCase();
    if (lowerStatus.includes('disposed')) return 'disposed';
    if (lowerStatus.includes('reserved')) return 'reserved';
    return 'pending';
  }

  private convertHistory(hearings: any[]): CaseHistory[] {
    return hearings.map((hearing, index) => ({
      id: hearing.id || index.toString(),
      date: hearing.date || new Date().toISOString(),
      purpose: hearing.purpose || hearing.cause_list_type || 'Unknown',
      order: hearing.order || null,
      nextPurpose: hearing.next_date || null,
      judge: hearing.judge,
    }));
  }

  // Utility methods for better error handling
  isNetworkError(error: string): boolean {
    return error.includes('fetch') || error.includes('network') || error.includes('connection');
  }

  isServerError(error: string): boolean {
    return error.includes('500') || error.includes('Internal server error');
  }

  isECourtError(error: string): boolean {
    return error.includes('eCourt') || error.includes('CAPTCHA') || error.includes('503');
  }

  // Retry mechanism for failed requests
  async retryRequest<T>(
    requestFn: () => Promise<ApiResponse<T>>,
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<ApiResponse<T>> {
    let lastError: string = '';
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      const result = await requestFn();
      
      if (!result.error) {
        return result;
      }
      
      lastError = result.error;
      
      // Don't retry client errors (4xx)
      if (result.error.includes('400') || result.error.includes('404')) {
        break;
      }
      
      if (attempt < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, delay * attempt));
      }
    }
    
    return { error: lastError };
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export individual functions for easier imports
export const {
  healthCheck,
  getCases,
  searchCases,
  getCase,
  addCase,
  updateCase,
  deleteCase,
  refreshCase,
  bulkRefreshCases,
  getRefreshStatus,
  searchCase,
  getCourts,
  getCaseTypes,
  getActTypes,
  getCaseStats,
  exportCases,
  convertSearchFormData,
  convertToLegalCase,
  retryRequest,
} = apiClient;
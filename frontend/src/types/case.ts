export interface LegalCase {
  id: string;
  caseNo: string;
  cnrNumber: string;
  caseType: string;
  petitioner: string;
  respondent: string;
  courtName: string;
  nextHearingDate: string | null;
  status: 'pending' | 'disposed' | 'reserved';
  filingDate: string;
  advocates: {
    petitioner: string;
    respondent: string;
  };
  history: CaseHistory[];
  syncCalendar: boolean;
  lastSyncedAt: string | null;
  // Enhanced fields from reference implementation
  registrationNumber?: string;
  registrationDate?: string;
  firstHearingDate?: string;
  decisionDate?: string;
  natureOfDisposal?: string;
  coram?: string;
  bench?: string;
  category?: string;
  subCategory?: string;
}

export interface CaseHistory {
  id: string;
  date: string;
  purpose: string;
  order: string | null;
  nextPurpose: string | null;
  judge?: string;
}

export type SearchType = 'cnr' | 'case' | 'party' | 'diary' | 'filing';

export interface SearchFormData {
  searchType: SearchType;
  cnrNumber?: string;
  caseType?: string;
  caseNumber?: string;
  year?: string;
  diaryNumber?: string;
  filingNumber?: string;
  partyName?: string;
  courtStateCode?: string;
  courtCode?: string;
}

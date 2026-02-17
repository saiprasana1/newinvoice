import apiClient from './client';

export const taxInvoiceApi = {
  // ============================================================================
  // Invoice State Management
  // ============================================================================
  
  /**
   * Get default state for a new tax invoice
   */
  getDefaultState: async () => {
    const response = await apiClient.get('/api/invoice/tax/default');
    return response.data;
  },

  /**
   * Clear invoice state (reset to defaults)
   */
  clearState: async () => {
    const response = await apiClient.post('/api/invoice/tax/clear');
    return response.data;
  },

  /**
   * Add a new empty row to the items table
   */
  addRow: async (currentState) => {
    const response = await apiClient.post('/api/invoice/tax/add-row', {
      state: currentState
    });
    return response.data;
  },

  /**
   * Process invoice with file upload and natural language command
   * @param {File} file - Excel/CSV file to process
   * @param {Object} currentState - Current invoice state
   * @param {string} command - Natural language command (e.g., "Add all details from dataset")
   */
  processInvoice: async (file, currentState, command) => {
    const formData = new FormData();
    
    if (file) {
      formData.append('file', file);
    }
    
    formData.append('state', JSON.stringify(currentState));
    formData.append('command', command || '');

    const response = await apiClient.post('/api/invoice/tax/process', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },

  /**
   * Export invoice to PDF or PNG
   * @param {Object} currentState - Current invoice state
   * @param {string} format - 'pdf' or 'png'
   */
  exportInvoice: async (currentState, format = 'pdf') => {
    const response = await apiClient.post('/api/invoice/tax/export', {
      state: currentState,
      format: format,
      template_name: 'Siva Sakthi GTA'
    }, {
      responseType: 'blob'
    });
    
    return response.data;
  },

  /**
   * Get HTML preview of the invoice
   */
  getHtmlPreview: async (currentState) => {
    const response = await apiClient.post('/api/invoice/tax/export', {
      state: currentState,
      format: 'html',
      template_name: 'Siva Sakthi GTA'
    });
    return response.data.html;
  },

  /**
   * Update fields from inline editing (sends partial edit + full state)
   */
  updateFieldsFromJson: async (editedJson, currentState) => {
    const response = await apiClient.post('/api/invoice/tax/update-fields', {
      edited_json: editedJson,
      state: currentState
    });
    return response.data;
  },

  /**
   * Delete a row by index
   */
  deleteRow: async (currentState, rowIndex) => {
    const response = await apiClient.post('/api/invoice/tax/delete-row', {
      state: currentState,
      row_index: rowIndex
    });
    return response.data;
  },

  /**
   * Save tax invoice state without exporting
   */
  saveState: async (currentState) => {
    const response = await apiClient.put('/api/invoice/tax/state', {
      state: currentState
    });
    return response.data;
  },

  // ============================================================================
  // Master Data - Parent Companies
  // ============================================================================

  /**
   * Get list of all parent companies
   */
  getParentCompanies: async () => {
    const response = await apiClient.get('/api/invoice/master-data/parent-companies');
    return response.data;
  },

  /**
   * Load parent company details into invoice state
   * @param {Object} currentState - Current invoice state
   * @param {string} companyId - Parent company ID
   */
  loadParentCompany: async (currentState, companyId) => {
    const response = await apiClient.post('/api/invoice/load-parent-company', {
      state: currentState,
      selected_id: companyId
    });
    return response.data;
  },

  // ============================================================================
  // Master Data - Client Companies
  // ============================================================================

  /**
   * Get list of all client companies
   */
  getClientCompanies: async () => {
    const response = await apiClient.get('/api/invoice/master-data/client-companies');
    return response.data;
  },

  /**
   * Load client company details into invoice state
   * @param {Object} currentState - Current invoice state
   * @param {string} companyId - Client company ID
   */
  loadClientCompany: async (currentState, companyId) => {
    const response = await apiClient.post('/api/invoice/load-client-company', {
      state: currentState,
      selected_id: companyId
    });
    return response.data;
  },

  // ============================================================================
  // Master Data - Bank Accounts
  // ============================================================================

  /**
   * Get list of all bank accounts
   */
  getBankAccounts: async () => {
    const response = await apiClient.get('/api/invoice/master-data/bank-accounts');
    return response.data;
  },

  /**
   * Load bank account details into invoice state
   * @param {Object} currentState - Current invoice state
   * @param {string} bankId - Bank account ID
   */
  loadBankAccount: async (currentState, bankId) => {
    const response = await apiClient.post('/api/invoice/load-bank-account', {
      state: currentState,
      selected_id: bankId
    });
    return response.data;
  },

  // ============================================================================
  // Master Data - Terms & Conditions
  // ============================================================================

  /**
   * Get list of all terms & conditions templates
   */
  getTermsAndConditions: async () => {
    const response = await apiClient.get('/api/invoice/master-data/terms-and-conditions');
    return response.data;
  },

  /**
   * Load terms & conditions into invoice state
   * @param {Object} currentState - Current invoice state
   * @param {string} tcId - Terms & Conditions ID
   */
  loadTermsAndConditions: async (currentState, tcId) => {
    const response = await apiClient.post('/api/invoice/load-terms-and-conditions', {
      state: currentState,
      selected_id: tcId
    });
    return response.data;
  },
};

import apiClient from './client';

export const billInvoiceApi = {
  // Get default invoice state
  getDefaultState: async () => {
    const response = await apiClient.get('/api/invoice/bill/default');
    return response.data;
  },

  // Clear invoice state (reset overrides)
  clearState: async () => {
    const response = await apiClient.post('/api/invoice/bill/clear');
    return response.data;
  },

  // Add a new empty row to the invoice
  addRow: async (currentState) => {
    const response = await apiClient.post('/api/invoice/bill/add-row', {
      state: currentState
    });
    return response.data;
  },

  // Process invoice with file upload and command
  processInvoice: async (file, currentState, command) => {
    const formData = new FormData();
    
    if (file) {
      formData.append('file', file);
    }
    
    formData.append('state', JSON.stringify(currentState));
    formData.append('command', command || '');

    const response = await apiClient.post('/api/invoice/bill/process', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },

  // Export invoice to PDF or PNG
  exportInvoice: async (currentState, format = 'pdf') => {
    const response = await apiClient.post('/api/invoice/bill/export', {
      state: currentState,
      format: format,
      template_name: 'Siva Sakthi Freight Bill'
    }, {
      responseType: 'blob' // Important for file download
    });
    
    return response.data;
  },

  // Get HTML Preview
  getHtmlPreview: async (currentState) => {
    const response = await apiClient.post('/api/invoice/bill/export', {
      state: currentState,
      format: 'html',
      template_name: 'Siva Sakthi Freight Bill'
    });
    return response.data.html;
  },

  // --- Master Data Endpoints ---

  // Get list of Parent Companies
  getParentCompanies: async () => {
    const response = await apiClient.get('/api/invoice/master-data/parent-companies');
    return response.data;
  },

  // Load Parent Company into state
  loadParentCompany: async (currentState, companyId) => {
    const response = await apiClient.post('/api/invoice/load-parent-company', {
      state: currentState,
      selected_id: companyId
    });
    return response.data;
  },

  // Get list of Client Companies
  getClientCompanies: async () => {
    const response = await apiClient.get('/api/invoice/master-data/client-companies');
    return response.data;
  },

  // Load Client Company into state
  loadClientCompany: async (currentState, companyId) => {
    const response = await apiClient.post('/api/invoice/load-client-company', {
      state: currentState,
      selected_id: companyId
    });
    return response.data;
  },

  // Update fields from inline editing
  updateFieldsFromJson: async (editedJson, currentState) => {
    const response = await apiClient.post('/api/invoice/bill/update-fields', {
      edited_json: editedJson,
      state: currentState
    });
    return response.data;
  },

  // Delete a row by index
  deleteRow: async (currentState, rowIndex) => {
    const response = await apiClient.post('/api/invoice/bill/delete-row', {
      state: currentState,
      row_index: rowIndex
    });
    return response.data;
  }
};

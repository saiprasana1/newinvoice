import React, { useState, useEffect } from 'react';
import { Building2, Loader2, AlertCircle } from 'lucide-react';
import { billInvoiceApi } from '../../api/billInvoiceApi';

const MasterDataLoader = ({ invoiceState, onStateUpdate }) => {
  const [parentCompanies, setParentCompanies] = useState([]);
  const [clientCompanies, setClientCompanies] = useState([]);
  const [loadingParents, setLoadingParents] = useState(true);
  const [loadingClients, setLoadingClients] = useState(true);
  
  const [isParentProcessing, setIsParentProcessing] = useState(false);
  const [isClientProcessing, setIsClientProcessing] = useState(false);

  const [selectedParent, setSelectedParent] = useState('');
  const [selectedClient, setSelectedClient] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const validateStateUpdate = (oldState, newState, fieldName) => {
    if (!newState || typeof newState !== 'object') {
      console.error(`Invalid state returned for ${fieldName}`);
      return false;
    }
    
    if (Object.keys(newState).length === 0) {
      console.error(`Empty state returned for ${fieldName}`);
      return false;
    }
    
    return true;
  };

  const showError = (message) => {
    setErrorMessage(message);
    setTimeout(() => setErrorMessage(''), 5000);
  };

  useEffect(() => {
    let mounted = true;

    const fetchData = async () => {
      try {
        const [parents, clients] = await Promise.all([
          billInvoiceApi.getParentCompanies(),
          billInvoiceApi.getClientCompanies()
        ]);

        if (mounted) {
          setParentCompanies(parents?.companies || []);
          setClientCompanies(clients?.companies || []);
        }
      } catch (err) {
        console.error('Failed to load master data:', err);
        if (mounted) {
          setParentCompanies([]);
          setClientCompanies([]);
        }
      } finally {
        if (mounted) {
          setLoadingParents(false);
          setLoadingClients(false);
        }
      }
    };

    fetchData();

    return () => {
      mounted = false;
    };
  }, []);

  const handleParentChange = async (e) => {
    const companyId = e.target.value;
    setSelectedParent(companyId);
    if (!companyId || !invoiceState) return;

    try {
      setIsParentProcessing(true);
      setErrorMessage('');
      
      const response = await billInvoiceApi.loadParentCompany(
        invoiceState,
        companyId
      );

      if (response?.state && validateStateUpdate(invoiceState, response.state, 'Parent Company')) {
        onStateUpdate(response.state);
      } else {
        showError('Failed to load parent company: Invalid response');
      }
    } catch (err) {
      console.error('Failed to load parent company:', err);
      showError('Failed to load parent company. Please try again.');
    } finally {
      setIsParentProcessing(false);
    }
  };

  const handleClientChange = async (e) => {
    const companyId = e.target.value;
    setSelectedClient(companyId);
    if (!companyId || !invoiceState) return;

    try {
      setIsClientProcessing(true);
      setErrorMessage('');
      
      const response = await billInvoiceApi.loadClientCompany(
        invoiceState,
        companyId
      );

      if (response?.state && validateStateUpdate(invoiceState, response.state, 'Client Company')) {
        onStateUpdate(response.state);
      } else {
        showError('Failed to load client company: Invalid response');
      }
    } catch (err) {
      console.error('Failed to load client company:', err);
      showError('Failed to load client company. Please try again.');
    } finally {
      setIsClientProcessing(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 mb-6">
      <h2 className="text-lg font-semibold mb-4 flex items-center">
        <Building2 className="h-5 w-5 mr-2 text-blue-600" />
        Company Details
      </h2>

      {errorMessage && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
          <p className="text-sm text-red-700">{errorMessage}</p>
        </div>
      )}

      <div className="space-y-4">
        {/* Parent Company Dropdown */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Parent Company (Biller)
          </label>
          <div className="relative">
            <select
              value={selectedParent}
              onChange={handleParentChange}
              disabled={loadingParents || isParentProcessing}
              className="w-full pl-3 pr-10 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
            >
              <option value="" disabled>
                Select Parent Company
              </option>

              {Array.isArray(parentCompanies) &&
                parentCompanies.map((company) => (
                  <option key={company.id} value={company.id}>
                    {company.label}
                  </option>
                ))}
            </select>

            {isParentProcessing && (
              <div className="absolute right-8 top-1/2 -translate-y-1/2">
                <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
              </div>
            )}
          </div>
        </div>

        {/* Client Company Dropdown */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Client Company (Billed To)
          </label>
          <div className="relative">
            <select
              value={selectedClient}
              onChange={handleClientChange}
              disabled={loadingClients || isClientProcessing}
              className="w-full pl-3 pr-10 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50"
            >
              <option value="" disabled>
                Select Client Company
              </option>

              {Array.isArray(clientCompanies) &&
                clientCompanies.map((company) => (
                  <option key={company.id} value={company.id}>
                    {company.label}
                  </option>
                ))}
            </select>
            {isClientProcessing && (
              <div className="absolute right-8 top-1/2 -translate-y-1/2">
                <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MasterDataLoader;

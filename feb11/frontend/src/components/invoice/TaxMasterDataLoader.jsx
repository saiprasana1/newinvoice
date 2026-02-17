import { useState, useEffect } from 'react';
import { Building2, Loader2, AlertCircle } from 'lucide-react';
import { taxInvoiceApi } from '../../api/taxInvoiceApi';

const TaxMasterDataLoader = ({ invoiceState, onStateUpdate }) => {
  const [parentCompanies, setParentCompanies] = useState([]);
  const [clientCompanies, setClientCompanies] = useState([]);
  const [bankAccounts, setBankAccounts] = useState([]);
  const [termsAndConditions, setTermsAndConditions] = useState([]);
  
  const [loadingParents, setLoadingParents] = useState(true);
  const [loadingClients, setLoadingClients] = useState(true);
  const [loadingBanks, setLoadingBanks] = useState(true);
  const [loadingTnC, setLoadingTnC] = useState(true);
  
  const [isParentProcessing, setIsParentProcessing] = useState(false);
  const [isClientProcessing, setIsClientProcessing] = useState(false);
  const [isBankProcessing, setIsBankProcessing] = useState(false);
  const [isTnCProcessing, setIsTnCProcessing] = useState(false);
  
  const [selectedParent, setSelectedParent] = useState('');
  const [selectedClient, setSelectedClient] = useState('');
  const [selectedBank, setSelectedBank] = useState('');
  const [selectedTnC, setSelectedTnC] = useState('');

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
        const [parents, clients, banks, tnc] = await Promise.all([
          taxInvoiceApi.getParentCompanies(),
          taxInvoiceApi.getClientCompanies(),
          taxInvoiceApi.getBankAccounts(),
          taxInvoiceApi.getTermsAndConditions()
        ]);

        if (mounted) {
          setParentCompanies(parents?.companies || []);
          setClientCompanies(clients?.companies || []);
          setBankAccounts(banks?.accounts || []);
          setTermsAndConditions(tnc?.terms || []);
        }
      } catch (err) {
        console.error('Failed to load master data:', err);
        if (mounted) {
          setParentCompanies([]);
          setClientCompanies([]);
          setBankAccounts([]);
          setTermsAndConditions([]);
        }
      } finally {
        if (mounted) {
          setLoadingParents(false);
          setLoadingClients(false);
          setLoadingBanks(false);
          setLoadingTnC(false);
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
      const response = await taxInvoiceApi.loadParentCompany(
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
      const response = await taxInvoiceApi.loadClientCompany(
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

  const handleBankChange = async (e) => {
    const bankId = e.target.value;
    setSelectedBank(bankId);
    if (!bankId || !invoiceState) return;

    try {
      setIsBankProcessing(true);
      setErrorMessage('');
      const response = await taxInvoiceApi.loadBankAccount(
        invoiceState,
        bankId
      );

      if (response?.state && validateStateUpdate(invoiceState, response.state, 'Bank Account')) {
        onStateUpdate(response.state);
      } else {
        showError('Failed to load bank account: Invalid response');
      }
    } catch (err) {
      console.error('Failed to load bank account:', err);
      showError('Failed to load bank account. Please try again.');
    } finally {
      setIsBankProcessing(false);
    }
  };

  const handleTnCChange = async (e) => {
    const tcId = e.target.value;
    setSelectedTnC(tcId);
    if (!tcId || !invoiceState) return;

    try {
      setIsTnCProcessing(true);
      setErrorMessage('');
      const response = await taxInvoiceApi.loadTermsAndConditions(
        invoiceState,
        tcId
      );

      if (response?.state && validateStateUpdate(invoiceState, response.state, 'Terms & Conditions')) {
        onStateUpdate(response.state);
      } else {
        showError('Failed to load terms & conditions: Invalid response');
      }
    } catch (err) {
      console.error('Failed to load terms & conditions:', err);
      showError('Failed to load terms & conditions. Please try again.');
    } finally {
      setIsTnCProcessing(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
      <h2 className="text-lg font-semibold mb-4 flex items-center">
        <Building2 className="h-5 w-5 mr-2 text-blue-600" />
        Company Details
      </h2>

      {errorMessage && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
          <AlertCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
          <p className="text-sm text-red-700">{errorMessage}</p>
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Parent Company
          </label>
          <div className="flex items-center gap-2">
            <select
              value={selectedParent}
              onChange={handleParentChange}
              disabled={loadingParents || isParentProcessing}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              <option value="">Select Parent Company</option>
              {Array.isArray(parentCompanies) &&
                parentCompanies.map((company) => (
                  <option key={company.id} value={company.id}>
                    {company.label}
                  </option>
                ))}
            </select>
            {isParentProcessing && (
              <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
            )}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Client Company
          </label>
          <div className="flex items-center gap-2">
            <select
              value={selectedClient}
              onChange={handleClientChange}
              disabled={loadingClients || isClientProcessing}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              <option value="">Select Client Company</option>
              {Array.isArray(clientCompanies) &&
                clientCompanies.map((company) => (
                  <option key={company.id} value={company.id}>
                    {company.label}
                  </option>
                ))}
            </select>
            {isClientProcessing && (
              <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
            )}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Bank Account
          </label>
          <div className="flex items-center gap-2">
            <select
              value={selectedBank}
              onChange={handleBankChange}
              disabled={loadingBanks || isBankProcessing}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              <option value="">Select Bank Account</option>
              {Array.isArray(bankAccounts) &&
                bankAccounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.label}
                  </option>
                ))}
            </select>
            {isBankProcessing && (
              <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
            )}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Terms & Conditions
          </label>
          <div className="flex items-center gap-2">
            <select
              value={selectedTnC}
              onChange={handleTnCChange}
              disabled={loadingTnC || isTnCProcessing}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              <option value="">Select Terms & Conditions</option>
              {Array.isArray(termsAndConditions) &&
                termsAndConditions.map((term) => (
                  <option key={term.id} value={term.id}>
                    {term.label}
                  </option>
                ))}
            </select>
            {isTnCProcessing && (
              <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaxMasterDataLoader;

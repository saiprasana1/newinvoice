import { useContext, useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, FileText, Image as ImageIcon, RotateCcw } from 'lucide-react';
import { InvoiceContext } from '../context/InvoiceContext';
import { taxInvoiceApi } from '../api/taxInvoiceApi';
import FileUpload from '../components/common/FileUpload';
import TaxInvoicePreview from '../components/invoice/TaxInvoicePreview';
import TaxMasterDataLoader from '../components/invoice/TaxMasterDataLoader';
import CommandInput from '../components/common/CommandInput';

const TaxInvoice = () => {
  const { taxInvoiceState, updateTaxInvoiceState, clearTaxInvoiceState } = useContext(InvoiceContext);
  const [invoiceState, setInvoiceState] = useState(taxInvoiceState);
  const [loading, setLoading] = useState(!taxInvoiceState);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  // Load default state on mount if not in context
  useEffect(() => {
    if (taxInvoiceState) {
      setInvoiceState(taxInvoiceState);
      setLoading(false);
    } else {
      const loadDefaultState = async () => {
        try {
          const defaultState = await taxInvoiceApi.getDefaultState();
          setInvoiceState(defaultState.state);
          updateTaxInvoiceState(defaultState.state);
        } catch (err) {
          console.error('Failed to load default state:', err);
          setError('Failed to load default invoice state. Is the backend running?');
        } finally {
          setLoading(false);
        }
      };

      loadDefaultState();
    }
  }, []);

  const handleStateUpdate = (newState) => {
    if (!newState) return;
    setInvoiceState(newState);
    updateTaxInvoiceState(newState);
  };

  const handleFileUpload = (file) => {
    if (!file) return;
    setSelectedFile(file);
    setError(null);
  };

  const handleCommand = async (command) => {
    if (!invoiceState) return;

    try {
      setProcessing(true);
      setError(null);
      
      const fileToProcess = selectedFile;
      
      const response = await taxInvoiceApi.processInvoice(
        fileToProcess,
        invoiceState,
        command
      );
      
      handleStateUpdate(response.state);
    } catch (err) {
      console.error('Command failed:', err);
      setError('Failed to process command');
    } finally {
      setProcessing(false);
    }
  };

  const handleExport = async (format) => {
    if (!invoiceState) return;

    try {
      setExporting(true);
      const blob = await taxInvoiceApi.exportInvoice(invoiceState, format);

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `tax_invoice.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Export failed:', err);
      setError('Failed to export invoice');
    } finally {
      setExporting(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm('Are you sure you want to reset? This will clear all current changes.')) {
      return;
    }

    try {
      setLoading(true);
      const response = await taxInvoiceApi.clearState();
      handleStateUpdate(response.state);
      clearTaxInvoiceState();
      setSelectedFile(null);
      setError(null);
    } catch (err) {
      console.error('Reset failed:', err);
      setError('Failed to reset invoice state');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
      <div className="w-full px-4 py-8">
      <div className="flex justify-between items-center mb-6 sticky top-0 bg-white z-10 -mx-4 px-4 py-4">
        <div className="flex-1">
          <Link
            to="/"
            className="text-gray-500 hover:text-gray-700 flex items-center mb-2"
          >
            <ArrowLeft className="h-4 w-4 mr-1" /> Back to Dashboard
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">
            Tax Invoice Generator
          </h1>
          <p className="text-gray-600 text-sm">
            Upload Excel file to generate professional tax invoices with GST calculations
          </p>
        </div>

        <div className="flex space-x-3">
          <button
            onClick={handleReset}
            disabled={loading || processing}
            className="flex items-center px-4 py-2 bg-red-50 border border-red-200 text-red-700 rounded-lg hover:bg-red-100 disabled:opacity-50"
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset
          </button>

          <button
            onClick={() => handleExport('pdf')}
            disabled={exporting || !invoiceState}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <FileText className="h-4 w-4 mr-2" />
            {exporting ? 'Exporting...' : 'Export PDF'}
          </button>

          <button
            onClick={() => handleExport('png')}
            disabled={exporting || !invoiceState}
            className="flex items-center px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            <ImageIcon className="h-4 w-4 mr-2" />
            {exporting ? 'Exporting...' : 'Export PNG'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <div className="lg:col-span-1 space-y-6">
          {invoiceState && (
            <TaxMasterDataLoader
              invoiceState={invoiceState}
              onStateUpdate={handleStateUpdate}
            />
          )}

          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold mb-4">Upload Data</h2>
            <FileUpload
              onUpload={handleFileUpload}
              isLoading={processing}
              error={error}
            />
            {selectedFile && (
              <div className="mt-3 p-2 bg-blue-50 border border-blue-100 rounded-md flex items-center">
                <FileText className="h-4 w-4 text-blue-600 mr-2" />
                <span className="text-sm text-blue-700 truncate">
                  {selectedFile.name}
                </span>
              </div>
            )}
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold mb-4">AI Commands</h2>
            <CommandInput
              onCommand={handleCommand}
              isLoading={processing}
            />
            <p className="text-xs text-gray-500 mt-3">
              Examples: "Extract all data", "Set invoice number to 123", "Update client name"
            </p>
          </div>
        </div>

        <div className="lg:col-span-3">
          {invoiceState && (
            <TaxInvoicePreview
              invoiceState={invoiceState}
              onStateUpdate={handleStateUpdate}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default TaxInvoice;

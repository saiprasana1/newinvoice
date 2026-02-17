import React, { useState, useRef, useEffect, useCallback } from 'react';
import { taxInvoiceApi } from '../../api/taxInvoiceApi';
import { Loader2, Plus } from 'lucide-react';
import { InvoiceRowManager } from '../../lib/invoiceRowManager';
import { deepMergeObjects } from '../../lib/mergeUtils';

function formatRelativeTime(date) {
  if (!date) return '';
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 10) return 'just now';
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ago`;
}

const TaxInvoicePreview = ({ invoiceState, onStateUpdate }) => {
  const [htmlContent, setHtmlContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [addingRow, setAddingRow] = useState(false);
  const [deletingRow, setDeletingRow] = useState(false);
  const [error, setError] = useState(null);
  const [syncing, setSyncing] = useState(false);
  const [lastSaved, setLastSaved] = useState(null);
  const [, forceUpdate] = useState(0);
  const previewContainerRef = useRef(null);
  const stateRef = useRef(invoiceState);
  const pendingEditsRef = useRef({});
  const isInitializedRef = useRef(false);
  const isInternalUpdateRef = useRef(false);
  const rowManagerRef = useRef(null);
  const editQueueRef = useRef([]);
  const syncingRef = useRef(false);

  // Re-render every 30s to keep relative time fresh
  useEffect(() => {
    if (!lastSaved) return;
    const interval = setInterval(() => forceUpdate(n => n + 1), 30000);
    return () => clearInterval(interval);
  }, [lastSaved]);

  const refreshHtmlPreview = useCallback(async (state) => {
    if (!state) return false;

    try {
      const html = await taxInvoiceApi.getHtmlPreview(state);
      setHtmlContent(html);
      setError(null);
      return true;
    } catch (err) {
      console.error('Failed to refresh preview:', err);
      setError('Failed to refresh invoice preview');
      return false;
    }
  }, []);

  useEffect(() => {
    stateRef.current = invoiceState;
    if (invoiceState && !isInternalUpdateRef.current) {
      refreshHtmlPreview(invoiceState);
    }
    isInternalUpdateRef.current = false;
  }, [invoiceState, refreshHtmlPreview]);

  const processEditQueue = useCallback(async () => {
    if (editQueueRef.current.length === 0) return;

    const queued = editQueueRef.current.splice(0);
    const merged = queued.reduce((acc, e) => deepMergeObjects(acc, e), {});

    syncingRef.current = true;
    setSyncing(true);
    isInternalUpdateRef.current = true;

    try {
      const response = await taxInvoiceApi.updateFieldsFromJson(
        merged,
        stateRef.current
      );
      if (response && response.state) {
        stateRef.current = response.state;
        if (onStateUpdate) onStateUpdate(response.state);
        await refreshHtmlPreview(response.state);
        rowManagerRef.current?.clearOriginals();
        setLastSaved(new Date());
        setError(null);
      }
    } catch (err) {
      console.error('Failed to sync queued edits:', err);
      rowManagerRef.current?.rollbackAll();
      setError('Failed to save changes');
    } finally {
      syncingRef.current = false;
      setSyncing(false);
    }

    if (editQueueRef.current.length > 0) {
      processEditQueue();
    }
  }, [refreshHtmlPreview, onStateUpdate]);

  const handleFieldEdit = useCallback(async (editedData) => {
    if (!editedData || Object.keys(editedData).length === 0) return;

    if (syncingRef.current) {
      editQueueRef.current.push(editedData);
      return;
    }

    try {
      syncingRef.current = true;
      setSyncing(true);
      isInternalUpdateRef.current = true;

      const currentState = stateRef.current;
      pendingEditsRef.current = deepMergeObjects(pendingEditsRef.current, editedData);

      const response = await taxInvoiceApi.updateFieldsFromJson(
        editedData,
        currentState
      );

      if (response && response.state) {
        stateRef.current = response.state;
        if (onStateUpdate) onStateUpdate(response.state);
        await refreshHtmlPreview(response.state);
        pendingEditsRef.current = {};
        rowManagerRef.current?.clearOriginals();
        setLastSaved(new Date());
        setError(null);
      }
    } catch (err) {
      console.error('Failed to sync field edit:', err);
      rowManagerRef.current?.rollbackAll();
      setError('Failed to save changes');
    } finally {
      syncingRef.current = false;
      setSyncing(false);
    }

    if (editQueueRef.current.length > 0) {
      processEditQueue();
    }
  }, [refreshHtmlPreview, onStateUpdate, processEditQueue]);

  const handleDeleteRow = useCallback(async (rowIndex) => {
    if (!stateRef.current || !onStateUpdate) return;

    try {
      setDeletingRow(true);
      isInternalUpdateRef.current = true;
      const response = await taxInvoiceApi.deleteRow(stateRef.current, rowIndex);
      if (response && response.state) {
        stateRef.current = response.state;
        onStateUpdate(response.state);
        setLastSaved(new Date());
      }
    } catch (err) {
      console.error('Failed to delete row:', err);
      setError('Failed to delete row');
    } finally {
      setDeletingRow(false);
    }
  }, [onStateUpdate]);

  useEffect(() => {
    if (!htmlContent || !previewContainerRef.current) return;

    if (isInitializedRef.current) {
      return;
    }

    const timer = setTimeout(() => {
      if (previewContainerRef.current) {
        rowManagerRef.current = new InvoiceRowManager({
          container: previewContainerRef.current,
          onDataChange: handleFieldEdit,
          onDelete: handleDeleteRow,
          invoiceType: 'tax'
        });
        rowManagerRef.current.init();
        isInitializedRef.current = true;
      }
    }, 150);

    return () => {
      clearTimeout(timer);
    };
  }, [htmlContent, handleFieldEdit, handleDeleteRow]);

  useEffect(() => {
    const initializePreview = async () => {
      if (!stateRef.current) return;

      try {
        setLoading(true);
        await refreshHtmlPreview(stateRef.current);
      } catch (err) {
        console.error('Failed to load preview:', err);
        setError('Failed to load invoice preview');
      } finally {
        setLoading(false);
      }
    };

    initializePreview();
  }, [refreshHtmlPreview]);

  useEffect(() => {
    return () => {
      if (rowManagerRef.current) {
        rowManagerRef.current.destroy();
        rowManagerRef.current = null;
      }
    };
  }, []);

  const handleAddRow = async () => {
    if (!stateRef.current || !onStateUpdate) return;

    try {
      setAddingRow(true);
      const response = await taxInvoiceApi.addRow(stateRef.current);
      stateRef.current = response.state;
      onStateUpdate(response.state);
      setLastSaved(new Date());
    } catch (err) {
      console.error('Failed to add row:', err);
      alert('Failed to add row');
    } finally {
      setAddingRow(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 bg-white rounded-lg border border-gray-200 shadow-sm">
        <Loader2 className="h-8 w-8 text-blue-600 animate-spin mb-4" />
        <p className="text-gray-500">Generating preview...</p>
      </div>
    );
  }

  if (error && !syncing) {
    return (
      <div className="flex items-center justify-center h-96 bg-red-50 rounded-lg border border-red-200">
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden border border-gray-200">
      <div className="bg-gray-50 px-4 py-2 border-b border-gray-200 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Live Preview</span>
          {syncing && <span className="text-xs text-blue-600 animate-pulse">Syncing...</span>}
          {deletingRow && <span className="text-xs text-red-600 animate-pulse">Deleting...</span>}
          {loading && <span className="text-xs text-amber-600 animate-pulse">Updating...</span>}
          {lastSaved && !syncing && !deletingRow && (
            <span className="text-xs text-green-600">Saved {formatRelativeTime(lastSaved)}</span>
          )}
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleAddRow}
            disabled={addingRow || loading || syncing || deletingRow}
            className="flex items-center px-2 py-1 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded border border-blue-200 transition-colors disabled:opacity-50"
            title="Add a new empty row to the invoice"
          >
            {addingRow ? (
              <Loader2 className="h-3 w-3 mr-1 animate-spin" />
            ) : (
              <Plus className="h-3 w-3 mr-1" />
            )}
            Add Row
          </button>
          <span className="text-xs text-gray-400">A4 Format</span>
        </div>
      </div>
      <div className="overflow-auto max-h-[800px] p-4 bg-gray-100 flex justify-center">
        <div
          ref={previewContainerRef}
          data-preview-container
          className="bg-white shadow-sm origin-top transform scale-90 md:scale-100 transition-transform"
          style={{ width: '210mm', minHeight: '297mm' }}
          dangerouslySetInnerHTML={{ __html: htmlContent }}
        />
      </div>
      <div className="bg-white px-4 py-2 border-t border-gray-200 text-xs text-gray-500">
        Click any field to edit. Press Enter to save, Tab to move to next field. Hover a row number to delete.
      </div>
    </div>
  );
};

export default TaxInvoicePreview;

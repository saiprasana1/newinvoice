import React, { createContext, useState, useCallback, useEffect } from 'react';

export const InvoiceContext = createContext();

export const InvoiceProvider = ({ children }) => {
  const [taxInvoiceState, setTaxInvoiceState] = useState(null);
  const [billInvoiceState, setBillInvoiceState] = useState(null);

  // Persist to localStorage
  useEffect(() => {
    if (taxInvoiceState) {
      localStorage.setItem('taxInvoiceState', JSON.stringify(taxInvoiceState));
    }
  }, [taxInvoiceState]);

  useEffect(() => {
    if (billInvoiceState) {
      localStorage.setItem('billInvoiceState', JSON.stringify(billInvoiceState));
    }
  }, [billInvoiceState]);

  const updateTaxInvoiceState = useCallback((newState) => {
    setTaxInvoiceState(newState);
  }, []);

  const updateBillInvoiceState = useCallback((newState) => {
    setBillInvoiceState(newState);
  }, []);

  const clearTaxInvoiceState = useCallback(() => {
    setTaxInvoiceState(null);
    localStorage.removeItem('taxInvoiceState');
  }, []);

  const clearBillInvoiceState = useCallback(() => {
    setBillInvoiceState(null);
    localStorage.removeItem('billInvoiceState');
  }, []);

  const value = {
    taxInvoiceState,
    billInvoiceState,
    updateTaxInvoiceState,
    updateBillInvoiceState,
    clearTaxInvoiceState,
    clearBillInvoiceState,
  };

  return (
    <InvoiceContext.Provider value={value}>
      {children}
    </InvoiceContext.Provider>
  );
};

import { useEffect } from 'react';
import { InvoiceRowManager } from '../lib/invoiceRowManager';

export const useInvoiceRowManager = (htmlContent, onDataChange) => {
  useEffect(() => {
    if (!htmlContent) return;

    const initRowManager = () => {
      if (InvoiceRowManager) {
        InvoiceRowManager.setOnDataChange(onDataChange);
        InvoiceRowManager.init(onDataChange);
      }
    };

    const timer = setTimeout(() => {
      initRowManager();
    }, 100);

    return () => {
      clearTimeout(timer);
    };
  }, [htmlContent, onDataChange]);
};

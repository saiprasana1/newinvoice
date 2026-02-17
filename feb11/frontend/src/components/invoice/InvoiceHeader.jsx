import React from 'react';
import { Calendar, FileText, Truck, CreditCard } from 'lucide-react';

const InvoiceHeader = ({ data }) => {
  if (!data) return null;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4 border-b pb-2">Invoice Details</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Bill Number */}
        <div className="space-y-1">
          <label className="text-xs font-medium text-gray-500 uppercase tracking-wider flex items-center">
            <FileText className="w-3 h-3 mr-1" />
            Bill Number
          </label>
          <div className="text-sm font-semibold text-gray-900">
            {data.series_no || <span className="text-gray-400 italic">Not set</span>}
          </div>
        </div>

        {/* Bill Date */}
        <div className="space-y-1">
          <label className="text-xs font-medium text-gray-500 uppercase tracking-wider flex items-center">
            <Calendar className="w-3 h-3 mr-1" />
            Bill Date
          </label>
          <div className="text-sm font-semibold text-gray-900">
            {data.bill_date || <span className="text-gray-400 italic">Not set</span>}
          </div>
        </div>

        {/* PO Number */}
        <div className="space-y-1">
          <label className="text-xs font-medium text-gray-500 uppercase tracking-wider flex items-center">
            <FileText className="w-3 h-3 mr-1" />
            PO Number
          </label>
          <div className="text-sm font-semibold text-gray-900">
            {data.po_no || <span className="text-gray-400 italic">Not set</span>}
          </div>
        </div>

        {/* PAN Number */}
        <div className="space-y-1">
          <label className="text-xs font-medium text-gray-500 uppercase tracking-wider flex items-center">
            <CreditCard className="w-3 h-3 mr-1" />
            PAN Number
          </label>
          <div className="text-sm font-semibold text-gray-900">
            {data.pan_no || <span className="text-gray-400 italic">Not set</span>}
          </div>
        </div>

        {/* Summary - Full Width */}
        <div className="col-span-1 md:grid-cols-2 lg:col-span-4 space-y-1">
          <label className="text-xs font-medium text-gray-500 uppercase tracking-wider flex items-center">
            <Truck className="w-3 h-3 mr-1" />
            Summary Description
          </label>
          <div className="text-sm font-medium text-gray-900 bg-gray-50 p-3 rounded border border-gray-100">
            {data.summary || <span className="text-gray-400 italic">No summary description available</span>}
          </div>
        </div>
      </div>
    </div>
  );
};

export default InvoiceHeader;

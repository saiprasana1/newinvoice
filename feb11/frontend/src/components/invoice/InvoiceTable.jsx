import React from 'react';

const InvoiceTable = ({ runs }) => {
  if (!runs || runs.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
        <p className="text-gray-500">No delivery runs found. Upload a file to add data.</p>
      </div>
    );
  }

  // Calculate totals
  const totalDCQty = runs.reduce((sum, run) => sum + (parseFloat(run.dc_qty_mt) || 0), 0);
  const totalGRQty = runs.reduce((sum, run) => sum + (parseFloat(run.gr_qty_mt) || 0), 0);
  const totalAmount = runs.reduce((sum, run) => sum + (parseFloat(run.line_total) || 0), 0);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Delivery Runs</h3>
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Truck No
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                LR No
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                DC Qty (MT)
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                GR Qty (MT)
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Rate
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Total
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {runs.map((run, index) => (
              <tr key={index} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {run.date}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                  {run.truck_no}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {run.lr_no}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                  {run.dc_qty_mt}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right font-medium">
                  {run.gr_qty_mt}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                  {run.rate}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right font-semibold">
                  {parseFloat(run.line_total).toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot className="bg-gray-50 font-semibold">
            <tr>
              <td colSpan="3" className="px-6 py-4 text-sm text-gray-900 text-right">
                Totals:
              </td>
              <td className="px-6 py-4 text-sm text-gray-900 text-right">
                {totalDCQty.toFixed(2)}
              </td>
              <td className="px-6 py-4 text-sm text-gray-900 text-right">
                {totalGRQty.toFixed(2)}
              </td>
              <td className="px-6 py-4 text-sm text-gray-900 text-right">
                -
              </td>
              <td className="px-6 py-4 text-sm text-blue-600 text-right text-base">
                {totalAmount.toFixed(2)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
};

export default InvoiceTable;

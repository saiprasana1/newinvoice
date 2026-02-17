import React from 'react';
import { Link } from 'react-router-dom';
import { Truck, FileText, ArrowRight } from 'lucide-react';

const Home = () => {
  return (
    <div className="space-y-8">
      <div className="text-center max-w-2xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          AI-Powered Invoice Generation
        </h1>
        <p className="text-lg text-gray-600">
          Upload your Excel files and let our AI extract the data, calculate totals, 
          and generate professional invoices in seconds.
        </p>
         {/* ✅ Guidance Button */}
  <div className="mt-6">
    <Link
      to="/guidance"
      className="inline-flex items-center px-6 py-2 border  border-gray-300 text-sm  font-bold  rounded-md text-white bg-black hover:bg-white hover:border-black hover:text-black transition"
    > 
      📘 How It Works
    </Link>
     </div>
      </div>

      

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto mt-12">
        {/* Bill Invoice Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 hover:shadow-md transition-shadow">
          <div className="bg-blue-100 w-12 h-12 rounded-lg flex items-center justify-center mb-6">
            <Truck className="w-6 h-6 text-blue-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Bill Invoice</h2>
          <p className="text-gray-600 mb-6">
            For freight and transportation bills. Extracts delivery runs, truck numbers, 
            and calculates totals based on MT quantity.
          </p>
          <Link
            to="/login" state={{ redirectTo: "/bill-invoice" }}
            className="inline-flex items-center justify-center w-full px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Create Bill Invoice
            <ArrowRight className="ml-2 w-4 h-4" />
          </Link>
        </div>

        {/* Tax Invoice Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 hover:shadow-md transition-shadow">
          <div className="bg-purple-100 w-12 h-12 rounded-lg flex items-center justify-center mb-6">
            <FileText className="w-6 h-6 text-purple-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Tax Invoice</h2>
          <p className="text-gray-600 mb-6">
            Standard tax invoices with GST calculations. Ideal for goods and services 
            billing with multiple line items.
          </p>
          <Link
            to="/login" state={{ redirectTo: "/tax-invoice" }}
            className="inline-flex items-center justify-center w-full px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
          >
            Create Tax Invoice
            <ArrowRight className="ml-2 w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Home;

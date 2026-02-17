import React from "react";
import { useNavigate } from "react-router-dom";

export default function Welcome() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen w-full bg-gradient-to-b from-black via-purple-900 to-purple-700 flex items-center justify-center px-6">
      
      <div className="text-center max-w-5xl">

        {/* Badge */}
        <div className="inline-block mb-6 px-4 py-2 rounded-full bg-white/10 backdrop-blur text-sm text-gray-200">
          🚀 JET Service Management System
        </div>

        {/* Main Heading */}
        <h1 className="text-5xl md:text-7xl font-extrabold leading-tight text-white">
      The Future of JET Services
     <br />
      Built With <span className="text-yellow-400">AI</span> &
      Intelligent <span className="text-yellow-400">Automation.</span>
       </h1>


        {/* Sub Text */}
        <p className="mt-6 text-lg md:text-xl text-gray-300 max-w-3xl mx-auto">
          Create, manage and export professional invoices,purchase order,inventory management,bill discount in seconds.
          Smart tracking, automated tax calculation and seamless billing —
          all in one powerful dashboard.
        </p>

        {/* Button */}
        <div className="mt-10">
          <button
            onClick={() => navigate("/services")}
            className="px-8 py-4 text-lg font-semibold rounded-xl bg-white text-black shadow-lg hover:scale-105 transition-all duration-300"
          >
            Explore Now →
          </button>
        </div>

      </div>
    </div>
  );
}

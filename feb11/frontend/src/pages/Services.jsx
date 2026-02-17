import React from "react";
import { useNavigate } from "react-router-dom";

export default function Services() {
  const navigate = useNavigate();

  const services = [
    {
      title: "Create Your AI-invoice",
      description:
        "Create, manage and export professional GST-compliant invoices in seconds with automated tax calculations.",
      image: "/ai-invoice.png",
      action: () => navigate("/dashboard"),
      reverse: false,
    },
    {
      title: "Inventory Management",
      description:
        "Monitor stock levels in real-time, manage products, and prevent shortages with intelligent tracking.",
      image: "/inventory.png",
      reverse: true,
    },
    {
      title: "Smart Purchase Order System",
      description:
        "Generate and manage purchase orders with vendor tracking, automated status updates, and streamlined workflow management.",
      image: "/purchase-order.png",
      reverse: false,
    },
    {
      title: "Flexible Bill Discount Engine",
      description:
        "Apply dynamic discount strategies and maintain full visibility of profit margins with automated calculations and reporting.",
      image: "/discount.png",
      reverse: true,
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-purple-900 to-purple-700 text-white">

      {/* ================= HERO SECTION ================= */}
      <div className="text-center py-20 px-6">
        <h1 className="text-4xl md:text-6xl font-bold mb-6">
          The Future of <span className="text-yellow-400">JET</span> Services
        </h1>

        <p className="text-lg text-gray-300 max-w-3xl mx-auto">
          Powerful invoice, inventory, purchase order and billing solutions —
          built with intelligent automation for modern businesses.
        </p>
      </div>
         <div className="text-lg text-gray-300 text-center mx-auto">
          <h4 className="text-4xl font-bold text-yellow-400">Our Services</h4>
         </div>
      {/* ================= SERVICES SECTION ================= */}
      <div className="max-w-6xl mx-auto px-6 py-16 space-y-24">

        {services.map((service, index) => (
          <div
            key={index}
            className={`flex flex-col md:flex ${
        service.reverse ? "md:flex-row-reverse" : "md:flex-row"
      } items-center gap-12`}
          >

            {/* IMAGE */}
            <div className="md:w-1/2">
        <img
          src={service.image}
          alt={service.title}
          className="w-full rounded-2xl shadow-2xl"
        />
      </div>

            {/* TEXT */}
             <div className="md:w-1/2">
        <h2 className="text-3xl md:text-4xl font-bold mb-6">
          {service.title}
        </h2>

        <p className="text-gray-300 text-lg leading-relaxed mb-6">
          {service.description}
        </p>

        {service.action && (
          <button
            onClick={service.action}
            className="text-yellow-400 text-xl font-semibold hover:underline"
          >
            Create Now
          </button>
        )}
      </div>

          </div>
        ))}

      </div>

{/* ================= FOOTER ================= */}
{/* ================= FOOTER ================= */}
<footer className="bg-gradient-to-b from-purple-700 via-purple-900 to-black py-14 text-center text-white">

  <div className="max-w-4xl mx-auto space-y-5 px-6">

    <h3 className="text-2xl font-bold">
      JET Business Solutions Pvt Ltd
    </h3>

    <p className="text-gray-300">
      D 46 CMDA Truck Terminal, Madhavaram, Chennai, Tamil Nadu 600110
    </p>

    <p className="text-gray-300">
      Email: support@jetbusiness.com
    </p>

    <p className="text-gray-300">
      Phone: +91 9999999999
    </p>

    <div className="pt-6 border-t border-white/20 text-sm text-gray-400">
      © {new Date().getFullYear()} JET Business Solutions Pvt Ltd. All Rights Reserved.
    </div>

  </div>

</footer>



</div> ); }

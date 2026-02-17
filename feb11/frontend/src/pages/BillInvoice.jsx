import { useContext, useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  FileText,
  Image as ImageIcon,
  RotateCcw,
  MessageCircle,
  X,
} from "lucide-react";

import { InvoiceContext } from "../context/InvoiceContext";
import { billInvoiceApi } from "../api/billInvoiceApi";
import FileUpload from "../components/common/FileUpload";
import InvoicePreview from "../components/invoice/InvoicePreview";
import CommandInput from "../components/common/CommandInput";
import MasterDataLoader from "../components/invoice/MasterDataLoader";

/* ===================== AI CHATBOT ===================== */


const BillInvoiceChatBot = () => {
  const steps = [
    "Step 1: Upload your Excel file from the Upload Data section.",
    "Step 2: Enter your AI command like 'Extract all data'.",
    "Step 3: Review the generated invoice preview on the right.",
    "Step 4: Export your invoice as PDF or PNG.",
  ];

  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [currentStep, setCurrentStep] = useState(-1);

  const chatRef = useRef(null);

  // Show welcome message when chat opens
  useEffect(() => {
    if (isOpen) {
      setMessages([
        { type: "bot", text: "Welcome 👋 How can I help you?" },
      ]);
      setCurrentStep(-1);
    }
  }, [isOpen]);

  // Auto-scroll when new messages are added
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTo({
        top: chatRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages]);

  const startGuide = () => {
    setMessages((prev) => [
      ...prev,
      { type: "user", text: "Show me how to generate bill invoice" },
      { type: "bot", text: steps[0] },
    ]);
    setCurrentStep(0);
  };

  const nextStep = () => {
    const next = currentStep + 1;

    if (next < steps.length) {
      setMessages((prev) => [
        ...prev,
        { type: "user", text: "Next Step" },
        { type: "bot", text: steps[next] },
      ]);
      setCurrentStep(next);
    } else {
      setMessages((prev) => [
        ...prev,
        { type: "bot", text: "🎉 You have completed all steps!" },
      ]);
      setCurrentStep(steps.length);
    }
  };

  const closeChat = () => {
    setIsOpen(false);
    setMessages([]);
    setCurrentStep(-1);
  };

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 bg-blue-600 text-white p-4 rounded-full shadow-xl hover:bg-blue-700 transition z-50"
      >
        {isOpen ? <X /> : <MessageCircle />}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-80 bg-black text-white rounded-2xl shadow-2xl flex flex-col overflow-hidden z-50">
          
          {/* Header */}
          <div className="bg-blue-600 p-4 font-semibold">
            AI Assistant
          </div>

          {/* Messages */}
          <div
            ref={chatRef}
            className="flex-1 p-4 space-y-3 overflow-y-auto max-h-96"
          >
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`p-3 rounded-lg text-sm ${
                  msg.type === "bot"
                    ? "bg-gray-800"
                    : "bg-blue-600 self-end"
                }`}
              >
                {msg.text}
              </div>
            ))}
          </div>

          {/* Action Buttons */}
          <div className="p-3 border-t border-gray-700 space-y-2">

            {/* Show Guide */}
            {currentStep === -1 && (
              <button
                onClick={startGuide}
                className="w-full bg-blue-600 hover:bg-blue-700 py-2 rounded-lg text-sm"
              >
                Show Guide
              </button>
            )}

            {/* Next Step */}
            {currentStep >= 0 && currentStep < steps.length && (
              <button
                onClick={nextStep}
                className="w-full bg-blue-600 hover:bg-blue-700 py-2 rounded-lg text-sm"
              >
                Next Step
              </button>
            )}

            {/* Close After Completion */}
            {currentStep === steps.length && (
              <button
                onClick={closeChat}
                className="w-full bg-red-600 hover:bg-red-700 py-2 rounded-lg text-sm"
              >
                Close
              </button>
            )}

          </div>
        </div>
      )}
    </>
  );
};

/* ===================== MAIN COMPONENT ===================== */

const BillInvoice = () => {
  const { billInvoiceState, updateBillInvoiceState, clearBillInvoiceState } =
    useContext(InvoiceContext);

  const [invoiceState, setInvoiceState] = useState(billInvoiceState);
  const [loading, setLoading] = useState(!billInvoiceState);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  useEffect(() => {
    if (billInvoiceState) {
      setInvoiceState(billInvoiceState);
      setLoading(false);
    } else {
      const loadDefaultState = async () => {
        try {
          const defaultState = await billInvoiceApi.getDefaultState();
          setInvoiceState(defaultState.state);
          updateBillInvoiceState(defaultState.state);
        } catch (err) {
          console.error("Failed to load default state:", err);
          setError("Failed to load default invoice state.");
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
    updateBillInvoiceState(newState);
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

      const response = await billInvoiceApi.processInvoice(
        selectedFile,
        invoiceState,
        command
      );

      handleStateUpdate(response.state);
    } catch (err) {
      console.error("Command failed:", err);
      setError("Failed to process command");
    } finally {
      setProcessing(false);
    }
  };

  const handleExport = async (format) => {
    if (!invoiceState) return;

    try {
      setExporting(true);
      const blob = await billInvoiceApi.exportInvoice(invoiceState, format);

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `bill_invoice.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error("Export failed:", err);
      setError("Failed to export invoice");
    } finally {
      setExporting(false);
    }
  };

  const handleReset = async () => {
    if (
      !window.confirm(
        "Are you sure you want to reset? This will clear all current changes."
      )
    ) {
      return;
    }

    try {
      setLoading(true);
      const response = await billInvoiceApi.clearState();
      handleStateUpdate(response.state);
      clearBillInvoiceState();
      setSelectedFile(null);
      setError(null);
    } catch (err) {
      console.error("Reset failed:", err);
      setError("Failed to reset invoice state");
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
    <div className="container mx-auto px-4 py-8">
      {/* HEADER */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <Link
            to="/"
            className="text-gray-500 hover:text-gray-700 flex items-center mb-2"
          >
            <ArrowLeft className="h-4 w-4 mr-1" /> Back to Dashboard
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">
            Bill Invoice Generator
          </h1>
          <p className="text-gray-600">
            Upload Excel file to generate freight bill
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
            onClick={() => handleExport("pdf")}
            disabled={exporting || !invoiceState}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <FileText className="h-4 w-4 mr-2" />
            {exporting ? "Exporting..." : "Export PDF"}
          </button>

          <button
            onClick={() => handleExport("png")}
            disabled={exporting || !invoiceState}
            className="flex items-center px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            <ImageIcon className="h-4 w-4 mr-2" />
            {exporting ? "Exporting..." : "Export PNG"}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* MAIN GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <div className="lg:col-span-1 space-y-6">
          {invoiceState && (
            <MasterDataLoader
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
              Examples: "Extract all data", "Set bill number to 123"
            </p>
          </div>
        </div>

        <div className="lg:col-span-3">
          {invoiceState && (
            <InvoicePreview
              invoiceState={invoiceState}
              onStateUpdate={handleStateUpdate}
            />
          )}
        </div>
      </div>

      {/* CHATBOT */}
      <BillInvoiceChatBot />
    </div>
  );
};

export default BillInvoice;

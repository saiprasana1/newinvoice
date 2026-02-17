// import { useState, useEffect } from "react";
// import { MessageCircle, X } from "lucide-react";

// const AIChatBot = ({ steps }) => {
//   const [isOpen, setIsOpen] = useState(false);
//   const [messages, setMessages] = useState([]);
//   const [currentStep, setCurrentStep] = useState(-1);

//   // Initialize welcome message when opening
//   useEffect(() => {
//     if (isOpen && messages.length === 0) {
//       setMessages([
//         {
//           type: "bot",
//           text: "Welcome 👋 How can I help you?",
//         },
//       ]);
//     }
//   }, [isOpen]);

//   // Start Guide
//   const handleStartGuide = () => {
//     setMessages((prev) => [
//       ...prev,
//       { type: "user", text: "Show me how it works" },
//       {
//         type: "bot",
//         text: "Great! Let's start with Step 1 👇",
//       },
//       {
//         type: "bot",
//         text: `Step 1: ${steps[0].title} - ${steps[0].description}`,
//       },
//     ]);
//     setCurrentStep(0);
//   };

//   // Next Step Handler
//   const handleNextStep = () => {
//     const nextStep = currentStep + 1;

//     if (nextStep < steps.length) {
//       setMessages((prev) => [
//         ...prev,
//         { type: "user", text: "Next Step" },
//         {
//           type: "bot",
//           text: `Step ${nextStep + 1}: ${steps[nextStep].title} - ${steps[nextStep].description}`,
//         },
//       ]);
//       setCurrentStep(nextStep);
//     } else {
//       setMessages((prev) => [
//         ...prev,
//         { type: "bot", text: "🎉 You have completed all the steps!" },
//       ]);
//       setCurrentStep(steps.length); // Mark as completed
//     }
//   };

//   // Close & Reset Chat
//   const handleCloseChat = () => {
//     setIsOpen(false);
//     setMessages([]);
//     setCurrentStep(-1);
//   };

//   return (
//     <>
//       {/* Floating Button */}
//       <button
//         onClick={() => setIsOpen(!isOpen)}
//         className="fixed bottom-6 right-6 bg-blue-600 text-white p-4 rounded-full shadow-xl hover:bg-blue-700 transition z-50"
//       >
//         {isOpen ? <X /> : <MessageCircle />}
//       </button>

//       {/* Chat Window */}
//       {isOpen && (
//         <div className="fixed bottom-24 right-6 w-80 bg-black text-white rounded-2xl shadow-2xl flex flex-col overflow-hidden z-50">

//           {/* Header */}
//           <div className="bg-blue-600 p-4 font-semibold">
//             AI Assistant
//           </div>

//           {/* Messages */}
//           <div className="flex-1 p-4 space-y-3 overflow-y-auto max-h-96">
//             {messages.map((msg, index) => (
//               <div
//                 key={index}
//                 className={`p-3 rounded-lg text-sm ${
//                   msg.type === "bot"
//                     ? "bg-gray-800 text-white"
//                     : "bg-blue-600 text-white self-end"
//                 }`}
//               >
//                 {msg.text}
//               </div>
//             ))}
//           </div>

//           {/* Action Buttons */}
//           <div className="p-3 border-t border-gray-700 space-y-2">

//             {/* Start Button */}
//             {currentStep === -1 && (
//               <button
//                 onClick={handleStartGuide}
//                 className="w-full bg-blue-600 hover:bg-blue-700 py-2 rounded-lg text-sm transition"
//               >
//                 Show Me How It Works
//               </button>
//             )}

//             {/* Next Step Button */}
//             {currentStep >= 0 && currentStep < steps.length && (
//               <button
//                 onClick={handleNextStep}
//                 className="w-full bg-blue-600 hover:bg-blue-700 py-2 rounded-lg text-sm transition"
//               >
//                 Next Step
//               </button>
//             )}

//             {/* Close Button After Completion */}
//             {currentStep === steps.length && (
//               <button
//                 onClick={handleCloseChat}
//                 className="w-full bg-red-600 hover:bg-red-700 py-2 rounded-lg text-sm transition"
//               >
//                 Close
//               </button>
//             )}

//           </div>
//         </div>
//       )}
//     </>
//   );
// };

// export default AIChatBot;


// import { useState, useEffect, useRef } from "react";
// import { MessageCircle, X } from "lucide-react";

// const AIChatBot = ({ steps, scrollToStep }) => {
//   const [isOpen, setIsOpen] = useState(false);
//   const [messages, setMessages] = useState([]);
//   const [currentStep, setCurrentStep] = useState(-1);
//   const messagesEndRef = useRef(null);

//   // Auto scroll chat to bottom
//   useEffect(() => {
//     messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
//   }, [messages]);

//   // Welcome message when opened
//   useEffect(() => {
//     if (isOpen && messages.length === 0) {
//       setMessages([
//         {
//           type: "bot",
//           text: "Welcome 👋 How can I help you?",
//         },
//       ]);
//     }
//   }, [isOpen]);

//   const resetChat = () => {
//     setIsOpen(false);
//     setMessages([]);
//     setCurrentStep(-1);
//   };

//   const handleStartGuide = () => {
//     scrollToStep(0);

//     setMessages((prev) => [
//       ...prev,
//       { type: "user", text: "Show me how it works" },
//       { type: "bot", text: "Great! Let's start 👇" },
//       {
//         type: "bot",
//         text: `Step 1: ${steps[0].title} - ${steps[0].description}`,
//       },
//     ]);

//     setCurrentStep(0);
//   };

//   const handleNextStep = () => {
//     const nextStep = currentStep + 1;

//     if (nextStep < steps.length) {
//       scrollToStep(nextStep);

//       setMessages((prev) => [
//         ...prev,
//         { type: "user", text: "Next Step" },
//         {
//           type: "bot",
//           text: `Step ${nextStep + 1}: ${steps[nextStep].title} - ${steps[nextStep].description}`,
//         },
//       ]);

//       setCurrentStep(nextStep);
//     } else {
//       setMessages((prev) => [
//         ...prev,
//         { type: "bot", text: "🎉 You completed all the steps!" },
//       ]);

//       setCurrentStep(steps.length);
//     }
//   };

//   return (
//     <>
//       {/* Floating Button */}
//       <button
//         onClick={() => setIsOpen(!isOpen)}
//         className="fixed bottom-6 right-6 bg-blue-600 text-white p-4 rounded-full shadow-xl hover:bg-blue-700 transition"
//       >
//         {isOpen ? <X /> : <MessageCircle />}
//       </button>

//       {/* Chat Window */}
//       {isOpen && (
//         <div className="fixed bottom-24 right-6 w-80 bg-black text-white rounded-2xl shadow-2xl flex flex-col overflow-hidden">

//           {/* Header */}
//           <div className="bg-blue-600 p-4 font-semibold flex justify-between items-center">
//             <span>AI Assistant</span>

//             {currentStep >= 0 && currentStep < steps.length && (
//               <span className="text-xs bg-white text-blue-600 px-2 py-1 rounded-full font-bold">
//                 {currentStep + 1} / {steps.length}
//               </span>
//             )}
//           </div>

//           {/* Messages */}
//           <div className="flex-1 p-4 space-y-3 overflow-y-auto max-h-96">
//             {messages.map((msg, index) => (
//               <div
//                 key={index}
//                 className={`p-3 rounded-lg text-sm ${
//                   msg.type === "bot"
//                     ? "bg-gray-800 text-white"
//                     : "bg-blue-600 text-white self-end"
//                 }`}
//               >
//                 {msg.text}
//               </div>
//             ))}
//             <div ref={messagesEndRef} />
//           </div>

//           {/* Buttons */}
//           <div className="p-3 border-t border-gray-700 space-y-2">

//             {currentStep === -1 && (
//               <button
//                 onClick={handleStartGuide}
//                 className="w-full bg-blue-600 hover:bg-blue-700 py-2 rounded-lg text-sm transition"
//               >
//                 Show Me How It Works
//               </button>
//             )}

//             {currentStep >= 0 && currentStep < steps.length && (
//               <button
//                 onClick={handleNextStep}
//                 className="w-full bg-blue-600 hover:bg-blue-700 py-2 rounded-lg text-sm transition"
//               >
//                 Next Step
//               </button>
//             )}

//             {currentStep === steps.length && (
//               <button
//                 onClick={resetChat}
//                 className="w-full bg-red-600 hover:bg-red-700 py-2 rounded-lg text-sm transition"
//               >
//                 Close
//               </button>
//             )}

//           </div>
//         </div>
//       )}
//     </>
//   );
// };

// export default AIChatBot;



import { useRef, useEffect, useState } from "react";

const AIChatBot = ({ steps, scrollToStep }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [currentStep, setCurrentStep] = useState(-1);

  const chatRef = useRef(null);

  // Reset when opened
  useEffect(() => {
    if (isOpen) {
      setMessages([{ type: "bot", text: "Welcome 👋 How can I help you?" }]);
      setCurrentStep(-1);
    }
  }, [isOpen]);

  // 🔥 AUTO SCROLL CHAT WINDOW
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
      { type: "user", text: "Show me how it works" },
      {
        type: "bot",
        text: `Step 1: ${steps[0].title} - ${steps[0].description}`,
      },
    ]);

    setCurrentStep(0);
    scrollToStep(0);
  };

  const nextStep = () => {
    const next = currentStep + 1;

    if (next < steps.length) {
      setMessages((prev) => [
        ...prev,
        { type: "user", text: "Next Step" },
        {
          type: "bot",
          text: `Step ${next + 1}: ${steps[next].title} - ${steps[next].description}`,
        },
      ]);

      setCurrentStep(next);
      scrollToStep(next);
    } else {
      setMessages((prev) => [
        ...prev,
        { type: "bot", text: "🎉 You completed all steps!" },
      ]);
      setCurrentStep(steps.length);
    }
  };

  return (
    <>
      {/* Floating Button */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col items-center">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="bg-blue-600 text-white p-4 rounded-full shadow-xl hover:bg-blue-700 transition"
        >
          {isOpen ? "✕" : "🤖"}
        </button>
      </div>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-80 bg-black text-white rounded-2xl shadow-2xl flex flex-col overflow-hidden z-50">
          <div className="bg-blue-600 p-4 font-semibold">
            AI Assistant
          </div>

          {/* 🔥 THIS IS THE IMPORTANT FIX */}
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

          <div className="p-3 border-t border-gray-700 space-y-2">
            {currentStep === -1 && (
              <button
                onClick={startGuide}
                className="w-full bg-blue-600 hover:bg-blue-700 py-2 rounded-lg text-sm transition"
              >
                Show Me How It Works
              </button>
            )}

            {currentStep >= 0 && currentStep < steps.length && (
              <button
                onClick={nextStep}
                className="w-full bg-blue-600 hover:bg-blue-700 py-2 rounded-lg text-sm transition"
              >
                Next Step
              </button>
            )}

            {currentStep === steps.length && (
              <button
                onClick={() => setIsOpen(false)}
                className="w-full bg-red-600 hover:bg-red-700 py-2 rounded-lg text-sm transition"
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

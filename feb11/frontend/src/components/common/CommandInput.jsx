import React, { useState } from 'react';
import { Send, Loader2 } from 'lucide-react';

const CommandInput = ({ onCommand, isLoading }) => {
  const [command, setCommand] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!command.trim() || isLoading) return;
    
    onCommand(command);
    setCommand('');
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <input
        type="text"
        value={command}
        onChange={(e) => setCommand(e.target.value)}
        placeholder="Ask AI to edit... (e.g., 'Set bill number to 123')"
        disabled={isLoading}
        className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white shadow-sm disabled:bg-gray-50 disabled:text-gray-400 transition-all"
      />
      <button
        type="submit"
        disabled={!command.trim() || isLoading}
        className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 text-blue-600 hover:bg-blue-50 rounded-full disabled:text-gray-300 disabled:hover:bg-transparent transition-colors"
      >
        {isLoading ? (
          <Loader2 className="h-5 w-5 animate-spin" />
        ) : (
          <Send className="h-5 w-5" />
        )}
      </button>
    </form>
  );
};

export default CommandInput;

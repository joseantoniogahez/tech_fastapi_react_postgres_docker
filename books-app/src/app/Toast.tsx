import React, { useEffect } from "react";

interface ToastProps {
  message: string;
  duration?: number;
  onClose: () => void;
}

const Toast: React.FC<ToastProps> = ({ message, duration = 5000, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  return (
    <div className="fixed bottom-6 right-24 bg-red-500 text-white px-4 py-2 rounded shadow-lg z-50">
      {message}
    </div>
  );
};

export default Toast;

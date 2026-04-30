import React from 'react';

interface GlassButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
}

const GlassButton: React.FC<GlassButtonProps> = ({ children, className = '', ...props }) => {
  return (
    <button className={`glass-button ${className}`} {...props}>
      {children}
    </button>
  );
};

export default GlassButton;

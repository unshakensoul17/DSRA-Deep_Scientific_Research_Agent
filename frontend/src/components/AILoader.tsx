import React, { useEffect, useState } from 'react';

interface AILoaderProps {
  currentAgent: string | null;
}

export const AILoader: React.FC<AILoaderProps> = ({ currentAgent }) => {
  const [dots, setDots] = useState('');

  useEffect(() => {
    const interval = setInterval(() => {
      setDots(prev => prev.length >= 3 ? '' : prev + '.');
    }, 400);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="ai-loader-container">
      <div className="ai-core">
        <div className="core-ring ring-1"></div>
        <div className="core-ring ring-2"></div>
        <div className="core-ring ring-3"></div>
        <div className="core-center">
          <div className="core-pulse"></div>
        </div>
        
        {/* Orbital nodes */}
        <div className="orbital-path path-1">
          <div className="node"></div>
        </div>
        <div className="orbital-path path-2">
          <div className="node"></div>
          <div className="node offset"></div>
        </div>
        <div className="orbital-path path-3">
          <div className="node"></div>
        </div>
      </div>
      
      <div className="status-container">
        <div className="status-badge">
          <span className="pulse-dot"></span>
          PIPELINE ACTIVE
        </div>
        <h4 className="agent-text">
          {currentAgent || 'Initializing System'}
        </h4>
        <p className="loading-text">
          Synthesizing literature resources{dots}
        </p>
      </div>

      <style>{`
        .ai-loader-container {
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          height: 100%;
          gap: 50px;
          perspective: 1000px;
        }

        .ai-core {
          position: relative;
          width: 240px;
          height: 240px;
          display: flex;
          justify-content: center;
          align-items: center;
          transform-style: preserve-3d;
          animation: float 6s ease-in-out infinite;
        }

        .core-center {
          position: absolute;
          width: 60px;
          height: 60px;
          background: radial-gradient(circle, var(--primary) 0%, transparent 70%);
          border-radius: 50%;
          box-shadow: 0 0 30px var(--primary), inset 0 0 20px var(--primary);
          z-index: 10;
        }

        .core-pulse {
          position: absolute;
          inset: -25px;
          border-radius: 50%;
          background: var(--primary);
          opacity: 0.2;
          animation: pulse 2s ease-out infinite;
        }

        .core-ring {
          position: absolute;
          border-radius: 50%;
          border: 1px solid rgba(99, 102, 241, 0.3);
          transform-style: preserve-3d;
        }

        .ring-1 {
          width: 130px;
          height: 130px;
          animation: spinX 8s linear infinite;
          border-color: rgba(99, 102, 241, 0.6);
          box-shadow: 0 0 20px rgba(99, 102, 241, 0.2);
        }

        .ring-2 {
          width: 180px;
          height: 180px;
          animation: spinY 12s linear infinite;
          border: 1px dashed rgba(99, 102, 241, 0.4);
        }

        .ring-3 {
          width: 230px;
          height: 230px;
          animation: spinZ 16s linear infinite;
          border-color: rgba(99, 102, 241, 0.2);
        }

        .orbital-path {
          position: absolute;
          border-radius: 50%;
          border: 1px solid transparent;
        }

        .path-1 { width: 150px; height: 150px; animation: orbit 5s linear infinite; }
        .path-2 { width: 200px; height: 200px; animation: orbit 8s linear infinite reverse; }
        .path-3 { width: 250px; height: 250px; animation: orbit 13s linear infinite; transform: rotateX(60deg); }

        .node {
          position: absolute;
          top: -3px;
          left: 50%;
          width: 6px;
          height: 6px;
          background: var(--primary);
          border-radius: 50%;
          box-shadow: 0 0 12px var(--primary), 0 0 24px var(--primary);
        }
        
        .node.offset {
          top: auto;
          bottom: -3px;
        }

        .status-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 14px;
        }

        .status-badge {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 6px 14px;
          background: rgba(99, 102, 241, 0.1);
          border: 1px solid rgba(99, 102, 241, 0.25);
          border-radius: 20px;
          font-family: monospace;
          font-size: 11px;
          color: var(--primary);
          letter-spacing: 1.5px;
          box-shadow: 0 0 15px rgba(99, 102, 241, 0.1);
        }

        .pulse-dot {
          width: 6px;
          height: 6px;
          background: var(--primary);
          border-radius: 50%;
          animation: blink 1s ease-in-out infinite;
          box-shadow: 0 0 8px var(--primary);
        }

        .agent-text {
          font-size: 20px;
          font-weight: 600;
          color: var(--text-main);
          margin: 0;
          text-shadow: 0 0 20px rgba(99, 102, 241, 0.3);
        }

        .loading-text {
          font-size: 13px;
          color: var(--text-muted);
          margin: 0;
          min-width: 240px;
          text-align: center;
        }

        @keyframes spinX { 0% { transform: rotateX(0deg) rotateY(0deg) rotateZ(0deg); } 100% { transform: rotateX(360deg) rotateY(180deg) rotateZ(90deg); } }
        @keyframes spinY { 0% { transform: rotateY(0deg) rotateZ(0deg) rotateX(0deg); } 100% { transform: rotateY(360deg) rotateZ(180deg) rotateX(90deg); } }
        @keyframes spinZ { 0% { transform: rotateZ(0deg) rotateX(0deg) rotateY(0deg); } 100% { transform: rotateZ(360deg) rotateX(180deg) rotateY(90deg); } }
        @keyframes orbit { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @keyframes pulse { 0% { transform: scale(1); opacity: 0.5; } 100% { transform: scale(2.8); opacity: 0; } }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
        @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-15px); } }
      `}</style>
    </div>
  );
};

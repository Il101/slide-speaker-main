import React from 'react';
import { CheckCircle } from 'lucide-react';

interface StepIndicatorProps {
  steps: string[];
  currentStep: number;
}

export const StepIndicator: React.FC<StepIndicatorProps> = ({ steps, currentStep }) => (
  <div className="flex items-center justify-center space-x-2">
    {steps.map((step, index) => (
      <React.Fragment key={index}>
        <div
          className={`flex items-center gap-2 transition-colors duration-200 ${
            index <= currentStep ? 'text-primary' : 'text-muted-foreground'
          }`}
        >
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200 ${
              index < currentStep
                ? 'bg-primary text-white'
                : index === currentStep
                ? 'bg-primary/20 text-primary border-2 border-primary'
                : 'bg-muted text-muted-foreground'
            }`}
          >
            {index < currentStep ? (
              <CheckCircle className="h-5 w-5" />
            ) : (
              <span className="text-sm font-medium">{index + 1}</span>
            )}
          </div>
          <span className="text-sm font-medium hidden sm:inline">{step}</span>
        </div>
        {index < steps.length - 1 && (
          <div
            className={`w-8 sm:w-12 h-0.5 transition-colors duration-200 ${
              index < currentStep ? 'bg-primary' : 'bg-muted'
            }`}
          />
        )}
      </React.Fragment>
    ))}
  </div>
);

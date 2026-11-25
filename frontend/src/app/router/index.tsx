import { createBrowserRouter } from 'react-router-dom';
import { AppLayout } from '../../components/layout/AppLayout';
import { OverviewView } from '../../features/overview/components/OverviewView';
import { VerificationView } from '../../features/verification/components/VerificationView';
import { WalletView } from '../../features/wallet/components/WalletView';
import { IssuerView } from '../../features/issuers/components/IssuerView';
import { IntelligenceView } from '../../features/intelligence/components/IntelligenceView';
import { LifecycleView } from '../../features/lifecycle/components/LifecycleView';
import { DeveloperNetworkView } from '../../features/developer/components/DeveloperNetworkView';
import { PlatformOperationsView } from '../../features/operations/components/PlatformOperationsView';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <OverviewView />,
      },
      {
        path: 'verify',
        element: <VerificationView />,
      },
      {
        path: 'wallet',
        element: <WalletView />,
      },
      {
        path: 'issuer',
        element: <IssuerView />,
      },
      {
        path: 'intelligence',
        element: <IntelligenceView />,
      },
      {
        path: 'lifecycle',
        element: <LifecycleView />,
      },
      {
        path: 'developer',
        element: <DeveloperNetworkView />,
      },
      {
        path: 'operations',
        element: <PlatformOperationsView />,
      },
    ],
  },
]);

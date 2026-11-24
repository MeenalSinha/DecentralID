import { createBrowserRouter } from 'react-router-dom';
import { AppLayout } from '../../components/layout/AppLayout';
import { VerificationView } from '../../features/verification/components/VerificationView';
import { WalletView } from '../../features/wallet/components/WalletView';
import { IssuerView } from '../../features/issuers/components/IssuerView';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
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
    ],
  },
]);

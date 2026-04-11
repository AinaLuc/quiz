import "./globals.css";

export const metadata = {
  title: "Cyvora | IA réceptionniste CVAC au Québec",
  description:
    "Cyvora aide les entreprises CVAC du Québec à répondre aux appels, planifier les rendez-vous et convertir plus de demandes grâce à l'IA.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="fr-CA">
      <body>
        {children}
        <footer className="site-footer" aria-label="Business information">
          <div className="site-footer-inner">
            <div className="site-footer-brand">
              <strong>BRANDEO AI LLC</strong>
              <span>Principal Office Address</span>
            </div>

            <div className="site-footer-copy">
              <p>
                <span>Type</span>
                <strong>Limited Liability Company</strong>
              </p>
              <p>
                <span>Charter No.</span>
                <strong>LC014508483</strong>
              </p>
              <p>
                <span>Domesticity</span>
                <strong>Domestic</strong>
              </p>
              <p>
                <span>Home State</span>
              </p>
              <p>
                <span>Registered Agent</span>
                <strong>INCORP SERVICES, INC.</strong>
              </p>
              <p>1531 E Bradford Pkwy</p>
              <p>Ste 200</p>
              <p>Springfield, MO 65804-6564</p>
              <p>
                <span>Status</span>
                <strong>Active</strong>
              </p>
              <p>
                <span>Date Formed</span>
                <strong>11/24/2023</strong>
              </p>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}

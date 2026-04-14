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
              <strong>MONINA</strong>
            </div>

            <div className="site-footer-copy">
              <p>
                <span>Registration number</span>
                <strong>1000451503</strong>
              </p>
              <p>
                <span>Business type</span>
                <strong>General Partnership</strong>
              </p>
              <p>6d - 7398 Yonge St, #1192, Thornhill, Ontario, L4J8J2</p>
              <p>
                <span>Country</span>
                <strong>Canada</strong>
              </p>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}

import "./globals.css";

export const metadata = {
  title: "报销智能初审 Agent",
  description: "交通、住宿、团建报销智能初审 MVP"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}

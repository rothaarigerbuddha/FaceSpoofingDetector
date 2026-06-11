import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import { getCookie } from "@/lib/cookieUtils";

const CommonLayout = async ({ children }: { children: React.ReactNode }) => {
  const token = await getCookie("access_token");
  const isLoggedIn = !!token;

  return (
    <>
      <Header isLoggedIn={isLoggedIn} />
      <main className="flex-1">{children}</main>
      <Footer />
    </>
  );
};

export default CommonLayout;

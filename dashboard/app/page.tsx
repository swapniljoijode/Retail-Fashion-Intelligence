import { redirect } from "next/navigation";

// Root redirects to the overview/sales page
export default function Home() {
  redirect("/sales");
}

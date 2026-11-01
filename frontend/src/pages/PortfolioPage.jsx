import { useParams } from "react-router-dom";
import ProfessionalPortfolio from "../components/ProfessionalPortfolio";

export default function PortfolioPage() {
  const { workerId } = useParams();
  return <main className="mx-auto w-full max-w-4xl py-8"><ProfessionalPortfolio workerId={workerId} /></main>;
}

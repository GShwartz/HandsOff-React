import logo from "../images/white.png";
import '../components/CSS/topnav.css';

function Topnav() {
    return (
        <nav className="navbar">
            <img src={logo} alt="White Logo" className="nav-logo" />

            <ul className="nav-list">
                <li className="nav-li">
                    <a href="/about" className="nav-link">Download Client</a>
                </li>
                <li className="nav-li">
                    <form action="/logout" method="post">
                        <input className="logout-button btn btn-danger" type="submit" value="Logout" />
                    </form>
                </li>
            </ul>
        </nav>
    );
}

export default Topnav;

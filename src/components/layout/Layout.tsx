import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'
import Footer from './Footer'
import styles from './Layout.module.css'

/**
 * Root layout — wraps every page with the shared Navbar and Footer.
 * The <Outlet /> is replaced by the matched page component.
 */
export default function Layout() {
  return (
    <div className={styles.wrapper}>
      <Navbar />
      <main className={styles.main}>
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}

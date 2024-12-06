import React from "react";
import Container from "./Container";

function Footer() {
  return (
    <footer className="bg-white shadow-inner flex flex-col items-center w-full py-5">
      <Container>
        <div className="text-sm text-gray-500  w-full text-center">
          © 2024 Your Company. All rights reserved.
        </div>
      </Container>
    </footer>
  );
}

export default Footer;

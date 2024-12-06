import React from "react";
import Container from "./Container";
import { Button } from "./ui/button";

function Navbar() {
  return (
    <nav className="bg-white shadow-md py-3 w-full fixed top-0 left-0 z-50">
      <Container>
        <div className="flex justify-between items-center">
          <div>Logo</div>
          <div className="flex ">
            <Button>Sign up</Button>
          </div>
        </div>
      </Container>
    </nav>
  );
}

export default Navbar;

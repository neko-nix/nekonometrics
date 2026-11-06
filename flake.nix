{
  description = "Entorno de desarrollo para seguimiento de inversiones en ETFs";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
    #nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system;
                                config.allowUnfree = true;
                              };
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Paquetes de NixOS
            sqlite

            #sqlitebrowser
            #sqlite-web
            # Paquetes de Python
            python314
            (python314.withPackages (ps: with ps; [
              pandas #pandas-datareader
              html5lib openpyxl
              numpy matplotlib
              yfinance plotly
              requests beautifulsoup4
              pytest
              seaborn
              tabulate
              kaleido
              pypdf
            ]))
          ];
          shellHook = ''
                      echo "Entorno de desarrolo activado :D"

                      # Borrar los caches de python
                      find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

                      tree -v --dirsfirst -I "__pycache__|__init__.py|__main__.py|flake.lock|apuntes.md|estructura.md|CHANGELOG.md|README.md|LICENSE"


          '';        
        };
      });
}



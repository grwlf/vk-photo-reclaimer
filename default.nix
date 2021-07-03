{ pkgs ?  import <nixpkgs> {}
, stdenv ? pkgs.stdenv
} :
let
  # self = pkgs.python36Packages;
  # inherit (self) buildPythonPackage fetchPypi;
in rec {
  mypython = pkgs.python37.withPackages (
    pp: let
      pyls = pp.python-language-server.override { providers=["pycodestyle"]; };
      pyls-mypy = pp.pyls-mypy.override { python-language-server=pyls; };
      vk-api = pp.buildPythonPackage rec {
        pname = "vk_api";
        version = "11.9.4";

        propagatedBuildInputs = with pp; [
          requests beautifulsoup4
          websocket_client six ];

        src = pp.fetchPypi {
          inherit pname version;
          sha256 = "sha256:18sa1mi3274piz7yjpmmbsv3irwpz7rlyiv2b3ssa171nhbpgqqz";
        };
      };
    in with pp; [
    ipython
    hypothesis
    pytest
    pytest-mypy
    coverage
    pyls
    pyls-mypy
    pyyaml
    wheel
    httplib2
    requests
    vk-api
    tqdm
    youtube-dl
    ipdb
  ]);

  shell = stdenv.mkDerivation {
    name = "buildenv";
    buildInputs =
      with pkgs;
      with self;
      [
        mypython
      ];

    shellHook = with pkgs; ''
      if test -f ./env.sh ; then
        . ./env.sh
      fi
    '';
  };
}

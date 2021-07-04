{ pkgs ?  import <nixpkgs> {}
, stdenv ? pkgs.stdenv
} :
let
  # self = pkgs.python36Packages;
  # inherit (self) buildPythonPackage fetchPypi;
in rec {

  pythondeps =
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
    httplib2
    requests
    vk-api
  ];

  mypython = pkgs.python37.withPackages (pp:
    (pythondeps pp) ++ (with pp; [
      wheel
      pyls
      pyls-mypy
      ipython
      hypothesis
      pytest
      pytest-mypy
      coverage
      pyyaml
      ipdb
      ]) );

  vk-photo-reclaimer = pkgs.python37.pkgs.buildPythonApplication {
    pname = "vk-photo-reclaimer";
    version = "1.0.0";
    src = ./src;
    # pythonPath = mypython.buildInputs;
    buildInputs = pythondeps pkgs.python37.pkgs;
    # pythonPath = with mypython.pkgs; [
    #   requests ipdb tqdm youtube-dl
    # ];
    # buildInputs = with mypython.paths; [ vk-api ];
    # patchPhase = ''
    #   for f in *py; do
    #     echo "Patching $f"
    #     sed -i "s|%DONGLEMAN_SPOOL%|\"${dongleman_spool}\"|g" "$f"
    #     sed -i "s|%DONGLEMAN_TGSESSION%|\"${telegram_session}\"|g" "$f"
    #     sed -i "s|%DONGLEMAN_SECRETS%|\"${python_secrets_json}\"|g" "$f"
    #   done
    # '';
    checkPhase = ''
      python3 ./vk_photo_reclaimer.py --help
    '';
    # doCheck = false;
  };

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

from metro_router.cli import main


def test_route_command_prints_legs_and_totals(capsys):
    assert main(["route", "Helwan", "Attaba"]) == 0
    out = capsys.readouterr().out
    assert "Helwan  ->  Attaba" in out
    assert "change at" in out
    assert "Transfers: 1" in out
    assert "Fare: 15 EGP" in out


def test_transfer_penalty_flag(capsys):
    main(["route", "Giza", "Safaa Hegazy"])
    default = capsys.readouterr().out
    main(["route", "Giza", "Safaa Hegazy", "--transfer-penalty", "0"])
    no_penalty = capsys.readouterr().out
    assert "Transfers: 1" in default
    assert "Transfers: 2" in no_penalty


def test_stations_for_one_line(capsys):
    assert main(["stations", "--line", "2"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("Line 2: Shubra El-Kheima <-> El-Mounib")
    assert "Attaba" in out and "change: Line 3" in out


def test_unknown_station_exits_with_error(capsys):
    assert main(["route", "Helwn", "Attaba"]) == 1
    err = capsys.readouterr().err
    assert "Unknown station 'Helwn'" in err
    assert "Helwan" in err


def test_unknown_line_exits_with_error(capsys):
    assert main(["stations", "--line", "9"]) == 1
    assert "Unknown line" in capsys.readouterr().err

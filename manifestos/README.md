# Manifesto Files Directory

Place manifesto documents in this directory using the following structure:

```
manifestos/
  {election-id}/
    {party-id}/
      manifesto.pdf     ← PDF scan of the original printed manifesto
      manifesto.txt     ← Plain text transcription, searchable
```

## Election IDs

| Display Year | Directory ID |
|---|---|
| 1945 | `1945` |
| 1950 | `1950` |
| 1951 | `1951` |
| 1955 | `1955` |
| 1959 | `1959` |
| 1964 | `1964` |
| 1966 | `1966` |
| 1970 | `1970` |
| February 1974 | `feb1974` |
| October 1974 | `oct1974` |
| 1979 | `1979` |
| 1983 | `1983` |
| 1987 | `1987` |
| 1992 | `1992` |
| 1997 | `1997` |
| 2001 | `2001` |
| 2005 | `2005` |
| 2010 | `2010` |
| 2015 | `2015` |
| 2017 | `2017` |
| 2019 | `2019` |
| 2024 | `2024` |

## Party IDs

| Party | Directory ID |
|---|---|
| Labour | `labour` |
| Conservative | `conservative` |
| Liberal / Liberal Democrat | `libdem` |
| Scottish National Party | `snp` |
| Green Party | `green` |
| UKIP | `ukip` |
| Reform UK | `reform` |
| Plaid Cymru | `plaid` |
| Democratic Unionist Party | `dup` |
| Sinn Féin | `sinnfein` |
| SDLP | `sdlp` |
| Alliance Party | `alliance` |

## Example

To add the 1997 Labour manifesto:
```
manifestos/1997/labour/manifesto.pdf
manifestos/1997/labour/manifesto.txt
```
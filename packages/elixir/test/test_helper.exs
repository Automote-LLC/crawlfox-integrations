exclude =
  if System.get_env("CRAWLFOX_API_KEY") in [nil, ""] do
    [:live]
  else
    []
  end

ExUnit.start(exclude: exclude)
